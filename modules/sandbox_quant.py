"""Sandbox Quant — data preload, Jupyter-style notebook cells, and execution."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit_ace import st_ace

from utils.data_engine import fetch_sandbox_data
from utils.sandbox_executor import run_sandbox_cells_through

DEFAULT_SANDBOX_TICKER = "AAPL"
CELLS_KEY = "sandbox_cells"
NEXT_CELL_ID_KEY = "sandbox_next_cell_id"
LAST_TICKER_KEY = "sandbox_last_ticker"

DEFAULT_SCRIPT_TEMPLATE = '''# Plantilla de Inteligencia Financiera - Universidad Iberoamericana
# El objeto 'data' ya contiene la información financiera del activo seleccionado.

print(f"--- Análisis Cuantitativo de {data['ticker']} ---")
print(f"Precio Actual: ${data['market_data']['current_price']}")
print(f"Beta del Activo: {data['market_data']['beta']}")
print(f"Tasa Libre de Riesgo (Rf) detectada: {data['macro_ratios']['risk_free_rate']}%")

# Intenta calcular un CAPM básico en el Sandbox:
# Ke = Rf + Beta * (Rm - Rf) -> Asumiendo Prima de Riesgo del 6%
rf = data['macro_ratios']['risk_free_rate'] / 100
beta = data['market_data']['beta']
mrp = 0.06

ke = rf + (beta * mrp)
print(f"Costo del Patrimonio estimado (CAPM): {round(ke * 100, 2)}%")
'''

NEW_CELL_TEMPLATE = "# Nueva celda\n"

# Ace auto-height: compact empty cells, grow with content, scroll after cap (Jupyter-like).
ACE_MIN_LINES = 3
ACE_MAX_LINES = 18


def _ace_line_bounds(code: str) -> tuple[int, int]:
    """Return (min_lines, max_lines) so the editor height tracks code length."""
    line_count = max(1, len((code or "").splitlines()))
    visible = min(max(ACE_MIN_LINES, line_count), ACE_MAX_LINES)
    return visible, ACE_MAX_LINES


def _new_cell(cell_id: int, code: str = NEW_CELL_TEMPLATE) -> dict:
    return {
        "id": cell_id,
        "code": code,
        "output": "",
        "success": True,
        "executed": False,
    }


def _ensure_notebook(ticker: str) -> None:
    """Initialize or reset notebook cells when ticker changes."""
    last = st.session_state.get(LAST_TICKER_KEY)
    cells = st.session_state.get(CELLS_KEY)

    if last != ticker or not cells:
        st.session_state[CELLS_KEY] = [
            _new_cell(1, DEFAULT_SCRIPT_TEMPLATE),
        ]
        st.session_state[NEXT_CELL_ID_KEY] = 2
        st.session_state[LAST_TICKER_KEY] = ticker
        for obsolete in ("sandbox_code_editor", "sandbox_run_result"):
            st.session_state.pop(obsolete, None)


def _fmt_compact(value: float) -> str:
    v = abs(float(value))
    if v >= 1e12:
        return f"{value / 1e12:.2f} T"
    if v >= 1e9:
        return f"{value / 1e9:.2f} Bn"
    if v >= 1e6:
        return f"{value / 1e6:.2f} MM"
    return f"{value:,.0f}"


def _render_cell_output(cell: dict, cell_number: int) -> None:
    if not cell.get("executed"):
        st.caption("Ejecuta esta celda para ver la salida.")
        return
    if cell["success"]:
        if (cell.get("output") or "").strip():
            st.code(cell["output"], language="text")
        else:
            st.code(
                "# El script corrió con éxito pero no generó salida (usa print()).",
                language="text",
            )
    else:
        if (cell.get("output") or "").strip():
            st.code(cell["output"], language="text")
        err = cell.get("error_message") or "Error desconocido"
        st.error(f"Error en la celda {cell_number}: {err}")


def _run_cell(cell_index: int, payload: dict) -> None:
    cells = st.session_state[CELLS_KEY]
    codes = [c["code"] for c in cells]
    results = run_sandbox_cells_through(codes, cell_index, payload)
    for j, result in enumerate(results):
        if j < len(cells):
            cells[j]["output"] = result.stdout
            cells[j]["success"] = result.success
            cells[j]["executed"] = True
            cells[j]["error_message"] = result.error_message
    if results and not results[-1].success:
        fail_idx = len(results) - 1
        for idx in range(fail_idx + 1, len(cells)):
            cells[idx]["executed"] = False
            cells[idx].pop("error_message", None)


def _render_notebook(payload: dict) -> None:
    st.markdown(f"##### Notebook Quant — **{payload['ticker']}**")

    cells: list[dict] = st.session_state[CELLS_KEY]
    can_delete = len(cells) > 1

    for i, cell in enumerate(cells):
        with st.container(border=True):
            prompt_col, code_col = st.columns(
                [1, 19],
                vertical_alignment="top",
                gap="small",
            )
            with prompt_col:
                st.markdown(
                    f'<div class="ibero-cell-prompt">[ {i + 1} ]:</div>',
                    unsafe_allow_html=True,
                )
                if can_delete and st.button(
                    "Eliminar",
                    key=f"sandbox_del_{cell['id']}",
                    help="Eliminar esta celda",
                    width="stretch",
                ):
                    cells.pop(i)
                    st.rerun()

            with code_col:
                min_lines, max_lines = _ace_line_bounds(cell["code"])
                edited = st_ace(
                    value=cell["code"],
                    language="python",
                    theme="chrome",
                    key=f"ace_editor_{cell['id']}",
                    height=None,
                    min_lines=min_lines,
                    max_lines=max_lines,
                    font_size=14,
                    tab_size=4,
                    wrap=True,
                    auto_update=True,
                )
                if edited is not None:
                    cell["code"] = edited

                if st.button(
                    "Ejecutar",
                    type="primary",
                    key=f"sandbox_run_{cell['id']}",
                    width="stretch",
                ):
                    _run_cell(i, payload)

                _render_cell_output(cell, i + 1)

    if st.button("+ Añadir celda", key="sandbox_add_cell", width="stretch"):
        next_id = st.session_state.get(NEXT_CELL_ID_KEY, len(cells) + 1)
        cells.append(_new_cell(next_id))
        st.session_state[NEXT_CELL_ID_KEY] = next_id + 1
        st.rerun()


def _render_data_preview(
    payload: dict,
    market: dict,
    metrics: dict,
    sources: dict,
    balance_sheet: pd.DataFrame,
    income_statement: pd.DataFrame,
    rf_pct: float,
) -> None:
    with st.expander("Vista previa de datos precargados", expanded=False):
        st.markdown("##### Métricas consolidadas (con fallbacks)")
        metrics_df = pd.DataFrame(
            [{"Métrica": k, "Valor": v} for k, v in metrics.items()]
        )
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### Balance (muestra)")
            if balance_sheet.empty:
                st.caption("Sin balance en Yahoo para este símbolo.")
            else:
                st.dataframe(balance_sheet.iloc[:8, :4], use_container_width=True)
        with col_b:
            st.markdown("##### Resultados (muestra)")
            if income_statement.empty:
                st.caption("Sin estado de resultados en Yahoo para este símbolo.")
            else:
                st.dataframe(income_statement.iloc[:8, :4], use_container_width=True)

        st.caption(
            f"Resumen: **{payload['ticker']}** · Precio {market['last_price']:,.2f} · "
            f"Beta {market['beta']:.2f} · Cap {_fmt_compact(market['market_cap'])} · "
            f"Rf {rf_pct:.2f}% · BS {sources.get('balance_sheet_period')} · "
            f"IS {sources.get('income_statement_period')}"
        )


def render() -> None:
    st.markdown(
        """
        <div class="ibero-hero">
            <h1>Sandbox Quant</h1>
            <p>
                Laboratorio cuantitativo con datos financieros precargados desde Yahoo Finance
                para experimentar con Python, CAPM, WACC y modelamiento sin fricción de setup.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ticker = (st.session_state.get("sandbox_ticker") or DEFAULT_SANDBOX_TICKER).strip().upper()

    try:
        payload = fetch_sandbox_data(ticker)
    except Exception as exc:
        st.error(f"No se pudo precargar **{ticker}**. {exc}")
        if ticker != DEFAULT_SANDBOX_TICKER:
            ticker = DEFAULT_SANDBOX_TICKER
            try:
                payload = fetch_sandbox_data(ticker)
            except Exception as exc2:
                st.error(f"Fallback **{ticker}** también falló. {exc2}")
                return
        else:
            return

    market = payload["market"]
    macro = payload["macro"]
    metrics = payload["metrics"]
    sources = payload["sources"]
    balance_sheet: pd.DataFrame = payload["balance_sheet"]
    income_statement: pd.DataFrame = payload["income_statement"]
    rf_pct = macro["risk_free_rate"] * 100.0

    _ensure_notebook(payload["ticker"])

    st.success(
        f"Activo precargado: **{payload['ticker']}** · "
        f"Precio {market['last_price']:,.2f} · Beta {market['beta']:.2f} · "
        f"Market cap {_fmt_compact(market['market_cap'])} · Rf {rf_pct:.2f}%."
    )

    _render_notebook(payload)

    _render_data_preview(
        payload, market, metrics, sources, balance_sheet, income_statement, rf_pct
    )
