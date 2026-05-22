"""Sandbox Quant — data preload, Jupyter-style notebook cells, and execution."""

from __future__ import annotations

import re
import uuid
import warnings

import pandas as pd
import streamlit as st
from streamlit_ace import st_ace

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from utils.data_engine import fetch_portfolio_data, fetch_sandbox_data
from utils.sandbox_executor import run_sandbox_cells_through

DEFAULT_SANDBOX_TICKER = "AAPL"
CELLS_KEY = "sandbox_cells"
LAST_TICKER_KEY = "sandbox_last_ticker"
ACTIVE_CELL_ID_KEY = "active_cell_id"
PORTFOLIO_DATA_KEY = "portfolio_data"
PORTFOLIO_MULTISELECT_KEY = "portfolio_multiselect_input"
PORTFOLIO_MULTISELECT_SYNC_KEY = "_portfolio_multiselect_sync"
PORTFOLIO_MANUAL_TICKER_KEY = "portfolio_manual_ticker"
SANDBOX_DATA_KEY = "sandbox_data"

TOP_TICKERS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "NVDA",
    "AMZN",
    "META",
    "TSLA",
    "ECOPETROL.CB",
    "PFBCOLOM.CB",
    "ISA.CB",
    "GEB.CB",
    "BTC-USD",
    "ETH-USD",
    "^GSPC",
    "^COLCAP",
]

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

# --- MÓDULO DE PORTAFOLIOS ---
# Si has cargado activos en el Gestor de Portafolio, están disponibles en el diccionario 'portfolio'.
# Ejemplo para crear un DataFrame consolidado con los precios de cierre:
#
# if portfolio:
#     precios_cierre = pd.DataFrame({ticker: df["Close"] for ticker, df in portfolio.items()})
#     print("Matriz de correlación del portafolio:")
#     print(precios_cierre.pct_change().corr())
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


def _new_cell_id() -> str:
    return str(uuid.uuid4())


def _cell_id_str(cell_id: str | int) -> str:
    return str(cell_id)


def _new_cell(cell_id: str, code: str = NEW_CELL_TEMPLATE) -> dict:
    return {
        "id": _cell_id_str(cell_id),
        "code": str(code),
        "output": "",
        "success": True,
        "executed": False,
    }


def _ensure_notebook(ticker: str) -> None:
    """Initialize or reset notebook cells when ticker changes."""
    last = st.session_state.get(LAST_TICKER_KEY)
    cells = st.session_state.get(CELLS_KEY)

    if last != ticker or not cells:
        first = _new_cell(_new_cell_id(), DEFAULT_SCRIPT_TEMPLATE)
        st.session_state[CELLS_KEY] = [first]
        st.session_state[ACTIVE_CELL_ID_KEY] = first["id"]
        st.session_state[LAST_TICKER_KEY] = ticker
        for obsolete in ("sandbox_code_editor", "sandbox_run_result", "sandbox_next_cell_id"):
            st.session_state.pop(obsolete, None)


def _prune_cell_widget_state(cell_id: str | int) -> None:
    """Remove Streamlit widget state for a deleted cell."""
    cid = _cell_id_str(cell_id)
    exact_keys = {
        f"ace_editor_{cid}",
        f"sandbox_select_{cid}",
        f"sandbox_run_mobile_{cid}",
    }
    for key in list(st.session_state.keys()):
        key_str = str(key)
        if key_str in exact_keys or (
            cid in key_str
            and any(
                token in key_str
                for token in (f"sandbox_cell_{cid}", f"sandbox_cell_body_{cid}")
            )
        ):
            st.session_state.pop(key, None)


def _cell_visual_styles(is_active: bool) -> tuple[str, str]:
    """Inline styles for Jupyter-like active cell (gold left bar + badge)."""
    if is_active:
        border_style = (
            "border-left: 5px solid #e8c042 !important; "
            "padding-left: 10px !important; "
            "border-top: 1px solid #e0e0e0 !important; "
            "border-right: 1px solid #e0e0e0 !important; "
            "border-bottom: 1px solid #e0e0e0 !important; "
            "border-radius: 4px !important; "
            "margin: 0 !important; "
            "background-color: #ffffff !important;"
        )
        badge_style = (
            "background-color: #e8c042 !important; "
            "color: #494646 !important; "
            "font-weight: bold; "
            "border-radius: 4px; "
            "padding: 4px 8px; "
            "display: inline-block; "
            "font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace; "
            "font-size: 0.85rem; "
            "text-align: center; "
            "min-width: 2.25rem; "
            "box-sizing: border-box;"
        )
    else:
        border_style = (
            "border: 1px solid #e0e0e0 !important; "
            "border-radius: 4px !important; "
            "padding-left: 14px !important; "
            "margin: 0 !important; "
            "background-color: #ffffff !important;"
        )
        badge_style = (
            "background-color: #f0f2f6; "
            "color: #494646; "
            "border-radius: 4px; "
            "padding: 4px 8px; "
            "display: inline-block; "
            "font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace; "
            "font-size: 0.85rem; "
            "text-align: center; "
            "min-width: 2.25rem; "
            "box-sizing: border-box;"
        )
    return border_style, badge_style


def _cell_style_css_fragment(
    cell_id: str,
    *,
    is_active: bool,
    is_first: bool,
) -> str:
    """Return CSS rules for one notebook cell (no Streamlit widget)."""
    border_style, badge_style = _cell_visual_styles(is_active)
    sep_rule = ""
    if not is_first:
        sep_rule = f"""
        div[data-testid="stVerticalBlock"][class*="st-key-sandbox_cell_{cell_id}"] {{
            border-top: 1px solid #e0e0e0;
            padding-top: 0.2rem;
            margin-top: 0;
        }}
        """
    first_cell_rule = ""
    if is_first:
        first_cell_rule = f"""
        div[data-testid="stVerticalBlock"][class*="st-key-sandbox_cell_{cell_id}"] {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        [class*="st-key-sandbox_cell_{cell_id}"]
        div[data-testid="stHorizontalBlock"] {{
            padding-top: 0 !important;
            margin-top: 0 !important;
        }}
        """
    return f"""
        {sep_rule}
        {first_cell_rule}
        [class*="st-key-sandbox_cell_{cell_id}"]
        div[data-testid="stHorizontalBlock"] {{
            {border_style}
        }}
        [class*="st-key-sandbox_cell_{cell_id}"] .ibero-sandbox-cell-badge {{
            {badge_style}
        }}
        [class*="st-key-sandbox_cell_{cell_id}"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:first-child {{
            position: relative;
        }}
        [class*="st-key-sandbox_cell_{cell_id}"] .ibero-sandbox-badge-wrap {{
            position: relative;
            display: flex;
            justify-content: flex-end;
            padding-top: 0.2rem;
            z-index: 2;
            pointer-events: none;
        }}
        [class*="st-key-sandbox_cell_{cell_id}"] .ibero-sandbox-cell-badge {{
            pointer-events: none;
        }}
        [class*="st-key-sandbox_cell_{cell_id}"]
        [class*="st-key-sandbox_select_{cell_id}"] {{
            position: absolute !important;
            top: 0.2rem;
            right: 0;
            left: 0;
            z-index: 3;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }}
        [class*="st-key-sandbox_cell_{cell_id}"]
        [class*="st-key-sandbox_select_{cell_id}"]
        [data-testid="stElementContainer"] {{
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }}
        [class*="st-key-sandbox_cell_{cell_id}"]
        [class*="st-key-sandbox_select_{cell_id}"] button {{
            width: 100% !important;
            min-height: 2rem !important;
            opacity: 0 !important;
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            cursor: pointer !important;
        }}
        """


def _inject_notebook_cells_styles(cells: list[dict], active_id: str) -> None:
    """Single style block for all cells — avoids empty markdown gaps per cell."""
    rules = "".join(
        _cell_style_css_fragment(
            _cell_id_str(cell["id"]),
            is_active=_cell_id_str(cell["id"]) == active_id,
            is_first=(i == 0),
        )
        for i, cell in enumerate(cells)
    )
    st.markdown(
        f'<div id="active-cell-run-trigger" class="ibero-sandbox-run-marker" '
        f'data-target="sandbox_tb_run" aria-hidden="true"></div>'
        f"<style>{rules}</style>"
        f'<span class="ibero-sandbox-styles-anchor" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )


def _set_active_cell_id(cell_id: str | int) -> None:
    st.session_state[ACTIVE_CELL_ID_KEY] = _cell_id_str(cell_id)


def _sync_active_cell(cells: list[dict]) -> int:
    """Resolve active cell index from ``active_cell_id``; repair invalid state."""
    if not cells:
        return 0
    legacy_idx = st.session_state.pop("sandbox_active_cell_idx", None)
    active_id = st.session_state.get(ACTIVE_CELL_ID_KEY)
    if active_id is None and legacy_idx is not None:
        legacy_idx = max(0, min(int(legacy_idx), len(cells) - 1))
        active_id = cells[legacy_idx]["id"]
    id_to_idx = {_cell_id_str(c["id"]): i for i, c in enumerate(cells)}
    active_key = _cell_id_str(active_id) if active_id is not None else ""
    if active_key not in id_to_idx:
        active_key = _cell_id_str(cells[0]["id"])
    st.session_state[ACTIVE_CELL_ID_KEY] = active_key
    return id_to_idx[active_key]


def _duplicate_cell(cells: list[dict], idx: int) -> None:
    source = cells[idx]
    new_cell = _new_cell(_new_cell_id(), str(source["code"]))
    cells.insert(idx + 1, new_cell)
    _set_active_cell_id(new_cell["id"])


def _insert_cell_relative(cells: list[dict], idx: int, *, above: bool) -> None:
    insert_at = idx if above else idx + 1
    new_cell = _new_cell(_new_cell_id(), NEW_CELL_TEMPLATE)
    cells.insert(insert_at, new_cell)
    _set_active_cell_id(new_cell["id"])


def _delete_cell(cells: list[dict], idx: int) -> None:
    if len(cells) > 1:
        removed_id = cells[idx]["id"]
        cells.pop(idx)
        _prune_cell_widget_state(removed_id)
        next_idx = min(idx, len(cells) - 1)
        _set_active_cell_id(cells[next_idx]["id"])
        return
    old_id = cells[0]["id"]
    cells[0] = _new_cell(_new_cell_id(), NEW_CELL_TEMPLATE)
    _prune_cell_widget_state(old_id)
    _set_active_cell_id(cells[0]["id"])


def _append_cell_at_end(cells: list[dict]) -> None:
    new_cell = _new_cell(_new_cell_id(), NEW_CELL_TEMPLATE)
    cells.append(new_cell)
    _set_active_cell_id(new_cell["id"])


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


def _parse_portfolio_tickers(text: str) -> list[str]:
    parts = re.split(r"[,;\s]+", (text or "").strip())
    return [part.strip().upper() for part in parts if part.strip()]


def _portfolio_multiselect_options(current_ticker: str) -> list[str]:
    options = list(TOP_TICKERS)
    ticker = (current_ticker or "").strip().upper()
    if ticker and ticker not in options:
        options.insert(0, ticker)
    portfolio_data = st.session_state.get(PORTFOLIO_DATA_KEY) or {}
    for symbol in portfolio_data:
        if symbol not in options:
            options.append(symbol)
    return options


def _portfolio_multiselect_default(current_ticker: str) -> list[str]:
    portfolio_data = st.session_state.get(PORTFOLIO_DATA_KEY) or {}
    if portfolio_data:
        return list(portfolio_data.keys())
    ticker = (current_ticker or DEFAULT_SANDBOX_TICKER).strip().upper()
    return [ticker] if ticker else []


def _merge_portfolio_selection(selected: list[str], manual_text: str) -> list[str]:
    merged = list(selected or [])
    for symbol in _parse_portfolio_tickers(manual_text):
        if symbol not in merged:
            merged.append(symbol)
    return merged


def _load_portfolio_to_kernel(tickers: list[str]) -> None:
    if not tickers:
        st.warning("Selecciona al menos un activo o añade un ticker manual.")
        return
    with st.spinner("Descargando series temporales del portafolio..."):
        result = fetch_portfolio_data(tickers)
    st.session_state[PORTFOLIO_DATA_KEY] = result.series
    for failed in result.failed:
        st.toast(f"No se pudo cargar: {failed}", icon="⚠️")
    if result.series:
        st.session_state[PORTFOLIO_MULTISELECT_SYNC_KEY] = list(result.series.keys())
        loaded = ", ".join(result.series.keys())
        st.success(f"Portafolio cargado: {loaded}")
        st.rerun()
    else:
        st.warning("Ningún activo del portafolio pudo cargarse.")


def _render_portfolio_panel(current_ticker: str) -> None:
    """Collapsible main-area panel to load multi-asset OHLCV into the notebook kernel."""
    ticker = (current_ticker or DEFAULT_SANDBOX_TICKER).strip().upper()
    portfolio_data = st.session_state.get(PORTFOLIO_DATA_KEY) or {}

    with st.expander(
        "💼 Gestor de Portafolio (Añadir Activos al Kernel)",
        expanded=False,
    ):
        with st.container(key="sandbox_portfolio_panel"):
            st.markdown(
                "<p style='color: #494646; font-size: 14px; margin-bottom: 0.75rem;'>"
                "Seleccione los instrumentos financieros que desea inyectar en el "
                "entorno de Python para análisis matricial o de portafolio.</p>",
                unsafe_allow_html=True,
            )
            if portfolio_data:
                st.caption(
                    f"{len(portfolio_data)} activo(s) en el kernel: "
                    f"{', '.join(portfolio_data.keys())}."
                )

            sync_selection = st.session_state.pop(PORTFOLIO_MULTISELECT_SYNC_KEY, None)
            if sync_selection is not None:
                st.session_state[PORTFOLIO_MULTISELECT_KEY] = sync_selection
            elif PORTFOLIO_MULTISELECT_KEY not in st.session_state:
                st.session_state[PORTFOLIO_MULTISELECT_KEY] = (
                    _portfolio_multiselect_default(ticker)
                )

            col_select, col_btn = st.columns([4, 1], vertical_alignment="bottom")
            with col_select:
                sub_ms, sub_manual = st.columns([3, 1], vertical_alignment="bottom")
                with sub_ms:
                    st.multiselect(
                        "Activos del Portafolio",
                        options=_portfolio_multiselect_options(ticker),
                        key=PORTFOLIO_MULTISELECT_KEY,
                        label_visibility="collapsed",
                    )
                with sub_manual:
                    st.text_input(
                        "Añadir otro ticker (manual)",
                        placeholder="ej. BABA",
                        key=PORTFOLIO_MANUAL_TICKER_KEY,
                        label_visibility="visible",
                    )
            with col_btn:
                if st.button(
                    "📥 Inyectar al Kernel",
                    type="secondary",
                    key="sandbox_load_portfolio",
                    width="stretch",
                ):
                    selected = st.session_state.get(PORTFOLIO_MULTISELECT_KEY, [])
                    manual = st.session_state.get(PORTFOLIO_MANUAL_TICKER_KEY, "")
                    tickers = _merge_portfolio_selection(selected, manual)
                    _load_portfolio_to_kernel(tickers)


def _run_cell(cell_index: int, payload: dict) -> None:
    cells = st.session_state[CELLS_KEY]
    codes = [c["code"] for c in cells]
    portfolio = st.session_state.get(PORTFOLIO_DATA_KEY) or {}
    results = run_sandbox_cells_through(
        codes,
        cell_index,
        payload,
        portfolio=portfolio,
    )
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


def _render_notebook_toolbar(
    cells: list[dict],
    payload: dict,
    *,
    active_idx: int,
) -> None:
    """Minimal global toolbar; actions apply to the active cell."""
    t1, t2, t3, t4, t5, t6, _sp = st.columns(
        [0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 8.8],
        gap="small",
        vertical_alignment="center",
    )

    if t1.button(
        "",
        key="sandbox_tb_run",
        help="Run active cell (Ctrl+Enter)",
        icon=":material/play_arrow:",
    ):
        _set_active_cell_id(cells[active_idx]["id"])
        _run_cell(active_idx, payload)
        st.rerun()

    if t2.button(
        "",
        key="sandbox_tb_dup",
        help="Duplicate active cell",
        icon=":material/content_copy:",
    ):
        _duplicate_cell(cells, active_idx)
        st.rerun()

    if t3.button(
        "",
        key="sandbox_tb_above",
        help="Add cell above",
        icon=":material/keyboard_arrow_up:",
    ):
        _insert_cell_relative(cells, active_idx, above=True)
        st.rerun()

    if t4.button(
        "",
        key="sandbox_tb_below",
        help="Add cell below",
        icon=":material/keyboard_arrow_down:",
    ):
        _insert_cell_relative(cells, active_idx, above=False)
        st.rerun()

    if t5.button(
        "",
        key="sandbox_tb_del",
        help="Delete active cell",
        icon=":material/delete:",
    ):
        _delete_cell(cells, active_idx)
        st.rerun()

    if t6.button(
        "",
        key="sandbox_tb_add_end",
        help="Add cell at end",
        icon=":material/add:",
    ):
        _append_cell_at_end(cells)
        st.rerun()

    with _sp:
        n = active_idx + 1
        total = len(cells)
        st.markdown(
            f'<p class="ibero-sandbox-toolbar-status">'
            f'<span class="ibero-sandbox-toolbar-status-inner">'
            f"<span>Active cell:</span>"
            f"<strong>{n}</strong>"
            f"<span>of</span>"
            f"<span>{total}</span>"
            f"</span></p>",
            unsafe_allow_html=True,
        )


def _render_notebook_cell(
    cell: dict,
    cell_index: int,
    payload: dict,
    *,
    is_active: bool,
) -> None:
    cell_id = _cell_id_str(cell["id"])
    _, badge_style = _cell_visual_styles(is_active)

    with st.container(key=f"sandbox_cell_{cell_id}"):
        prompt_col, code_col = st.columns(
            [1, 19],
            vertical_alignment="top",
            gap="small",
        )
        with prompt_col:
            st.markdown(
                f'<div class="ibero-sandbox-badge-wrap">'
                f'<div class="ibero-sandbox-cell-badge" style="{badge_style}">'
                f"[{cell_index + 1}]</div></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"[ {cell_index + 1} ]",
                key=f"sandbox_select_{cell_id}",
                help=f"Select cell {cell_index + 1}",
                type="secondary",
                width="stretch",
            ):
                _set_active_cell_id(cell_id)
                st.rerun()

        with code_col:
            with st.container(key=f"sandbox_cell_body_{cell_id}"):
                min_lines, max_lines = _ace_line_bounds(cell["code"])
                edited = st_ace(
                    value=cell["code"],
                    language="python",
                    theme="chrome",
                    key=f"ace_editor_{cell_id}",
                    height=None,
                    min_lines=min_lines,
                    max_lines=max_lines,
                    font_size=14,
                    tab_size=4,
                    wrap=True,
                    auto_update=True,
                )
                if edited is not None and edited != cell["code"]:
                    cell["code"] = edited
                    if not is_active:
                        _set_active_cell_id(cell_id)
                        st.rerun()

                if st.button(
                    "Run cell",
                    type="secondary",
                    key=f"sandbox_run_mobile_{cell_id}",
                    width="stretch",
                    help="Run this cell",
                ):
                    _set_active_cell_id(cell_id)
                    _run_cell(cell_index, payload)
                    st.rerun()

                _render_cell_output(cell, cell_index + 1)


_KEYBOARD_RUN_BRIDGE_HTML = """
<html><head><style>html,body{margin:0;padding:0;height:0;overflow:hidden;}</style></head>
<body>
<div data-ibero-bridge="keyboard-run" hidden aria-hidden="true"></div>
<script>
(function () {
    const parentWin = window.parent;
    const doc = parentWin.document;

    function resolveToolbarRunButton() {
        const primary = doc.querySelector('[class*="st-key-sandbox_tb_run"] button');
        if (primary) {
            return primary;
        }
        const marker = doc.getElementById("active-cell-run-trigger");
        if (!marker) {
            return null;
        }
        const toolbarHost = marker.closest('[class*="st-key-sandbox_tb_run"]')
            || marker.closest('div[data-testid="stHorizontalBlock"]');
        if (!toolbarHost) {
            return null;
        }
        return toolbarHost.querySelector("button");
    }

    function cellIdFromHost(host) {
        if (!host) {
            return null;
        }
        const parts = (host.className ? String(host.className) : "").split(/\s+/);
        for (const part of parts) {
            if (part.includes("st-key-sandbox_cell_body_")) {
                return part.split("st-key-sandbox_cell_body_")[1] || null;
            }
            if (part.includes("st-key-sandbox_cell_")) {
                return part.split("st-key-sandbox_cell_")[1] || null;
            }
        }
        return null;
    }

    function cellHostFromFrame(frame) {
        let el = frame;
        while (el && el !== doc.body) {
            const cls = el.className ? String(el.className) : "";
            if (cls.includes("st-key-sandbox_cell_body_")) {
                el = el.parentElement;
                continue;
            }
            if (cls.includes("st-key-sandbox_cell_")) {
                return el;
            }
            el = el.parentElement;
        }
        return null;
    }

    function isHostVisuallyActive(host) {
        const row = host && host.querySelector('[data-testid="stHorizontalBlock"]');
        if (!row) {
            return false;
        }
        const left = parseFloat(getComputedStyle(row).borderLeftWidth || "0");
        return left >= 4;
    }

    function syncActiveCellFromHost(host) {
        const cellId = cellIdFromHost(host);
        if (!cellId) {
            return;
        }
        if (parentWin.__iberoFocusedCellId === cellId) {
            return;
        }
        if (isHostVisuallyActive(host)) {
            parentWin.__iberoFocusedCellId = cellId;
            return;
        }
        const selectBtn = host.querySelector('[class*="st-key-sandbox_select_"] button');
        if (!selectBtn) {
            return;
        }
        parentWin.__iberoFocusedCellId = cellId;
        selectBtn.click();
    }

    function onEditorFocusIn(e) {
        const frame = e.view && e.view.frameElement;
        if (!frame || !doc.contains(frame)) {
            return;
        }
        const host = cellHostFromFrame(frame);
        if (!host) {
            return;
        }
        syncActiveCellFromHost(host);
    }

    function runButtonForCellHost(host) {
        if (!host) {
            return null;
        }
        const perCell = host.querySelector('[class*="st-key-sandbox_run_mobile_"] button');
        if (perCell) {
            return perCell;
        }
        return resolveToolbarRunButton();
    }

    function resolveRunButton(e) {
        const view = e && e.view;
        const frame = view && view.frameElement;
        if (frame && doc.contains(frame)) {
            try {
                const idoc = frame.contentDocument || view.document;
                if (idoc && idoc.querySelector("[data-ibero-bridge]")) {
                    return resolveToolbarRunButton();
                }
            } catch (err) {
                /* ignore */
            }
            const host = cellHostFromFrame(frame);
            const cellBtn = runButtonForCellHost(host);
            if (cellBtn) {
                return cellBtn;
            }
        }
        return resolveToolbarRunButton();
    }

    function triggerRunCell(e) {
        if (!((e.ctrlKey || e.metaKey) && e.key === "Enter")) {
            return;
        }
        e.preventDefault();
        e.stopPropagation();
        const btn = resolveRunButton(e);
        if (btn) {
            btn.click();
        }
    }

    function isBridgeIframe(frame) {
        try {
            const idoc = frame.contentDocument;
            return Boolean(idoc && idoc.querySelector("[data-ibero-bridge]"));
        } catch (err) {
            return false;
        }
    }

    function bindAceIframes() {
        doc.querySelectorAll("iframe").forEach((frame) => {
            if (isBridgeIframe(frame)) {
                return;
            }
            try {
                const idoc = frame.contentDocument || frame.contentWindow?.document;
                if (!idoc || idoc.querySelector("[data-ibero-bridge]")) {
                    return;
                }
                if (idoc.__iberoRunHandler) {
                    idoc.removeEventListener("keydown", idoc.__iberoRunHandler, true);
                }
                if (idoc.__iberoFocusHandler) {
                    idoc.removeEventListener("focusin", idoc.__iberoFocusHandler, true);
                    idoc.removeEventListener("mousedown", idoc.__iberoFocusHandler, true);
                }
                idoc.__iberoRunHandler = triggerRunCell;
                idoc.__iberoFocusHandler = onEditorFocusIn;
                idoc.addEventListener("keydown", triggerRunCell, true);
                idoc.addEventListener("focusin", onEditorFocusIn, true);
                idoc.addEventListener("mousedown", onEditorFocusIn, true);
            } catch (err) {
                /* cross-origin iframe */
            }
        });
    }

    function scheduleAceBind() {
        bindAceIframes();
        window.setTimeout(bindAceIframes, 250);
        window.setTimeout(bindAceIframes, 800);
    }

    const hub = parentWin.__iberoSandboxRunShortcut;
    if (hub && hub.handler) {
        doc.removeEventListener("keydown", hub.handler, true);
    }
    parentWin.__iberoSandboxRunShortcut = { handler: triggerRunCell };
    doc.addEventListener("keydown", triggerRunCell, true);
    scheduleAceBind();

    if (parentWin.__iberoSandboxRunObserver) {
        parentWin.__iberoSandboxRunObserver.disconnect();
    }
    parentWin.__iberoSandboxRunObserver = new MutationObserver(scheduleAceBind);
    parentWin.__iberoSandboxRunObserver.observe(doc.body, {
        childList: true,
        subtree: true,
    });
})();
</script>
</body></html>
"""


def _render_keyboard_run_bridge() -> None:
    """Inject Ctrl/Cmd+Enter listener (toolbar or focused Ace cell)."""
    with st.container(key="sandbox_kbd_bridge"):
        # st.iframe rejects height=0; "content" auto-sizes minimal HTML (Streamlit 1.56+).
        if hasattr(st, "iframe"):
            st.iframe(_KEYBOARD_RUN_BRIDGE_HTML, height="content")
            return
        import streamlit.components.v1 as components

        components.html(_KEYBOARD_RUN_BRIDGE_HTML, height=1)


def _render_notebook(payload: dict) -> None:
    st.markdown(f"##### Notebook Quant — **{payload['ticker']}**")

    cells: list[dict] = st.session_state[CELLS_KEY]
    active_idx = _sync_active_cell(cells)
    active_id = _cell_id_str(st.session_state[ACTIVE_CELL_ID_KEY])

    with st.container(border=False, key="sandbox_notebook_panel"):
        _render_notebook_toolbar(cells, payload, active_idx=active_idx)
        _inject_notebook_cells_styles(cells, active_id)

        for i, cell in enumerate(cells):
            _render_notebook_cell(
                cell,
                i,
                payload,
                is_active=(_cell_id_str(cell["id"]) == active_id),
            )

        _render_keyboard_run_bridge()


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
        st.dataframe(metrics_df, width="stretch", hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### Balance (muestra)")
            if balance_sheet.empty:
                st.caption("Sin balance en Yahoo para este símbolo.")
            else:
                st.dataframe(balance_sheet.iloc[:8, :4], width="stretch")
        with col_b:
            st.markdown("##### Resultados (muestra)")
            if income_statement.empty:
                st.caption("Sin estado de resultados en Yahoo para este símbolo.")
            else:
                st.dataframe(income_statement.iloc[:8, :4], width="stretch")

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
            <p class="ibero-hero-heading">Sandbox Quant</p>
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

    st.session_state[SANDBOX_DATA_KEY] = payload
    _ensure_notebook(payload["ticker"])

    success_msg = (
        f"Activo precargado: **{payload['ticker']}** · "
        f"Precio {market['last_price']:,.2f} · Beta {market['beta']:.2f} · "
        f"Market cap {_fmt_compact(market['market_cap'])} · Rf {rf_pct:.2f}%."
    )
    portfolio_data = st.session_state.get(PORTFOLIO_DATA_KEY) or {}
    if portfolio_data:
        success_msg += (
            f" Portafolio en kernel: {', '.join(portfolio_data.keys())}."
        )
    st.success(success_msg)

    _render_portfolio_panel(payload["ticker"])

    _render_data_preview(
        payload, market, metrics, sources, balance_sheet, income_statement, rf_pct
    )

    _render_notebook(payload)
