"""Motor de Valoración: DCF / WACC con simulación interactiva."""

from __future__ import annotations

import streamlit as st

from utils.data_engine import (
    DEFAULT_ERP,
    DEFAULT_FCF_GROWTH,
    DEFAULT_TERMINAL_G,
    build_valuation_inputs,
    fetch_ticker_info,
)
from utils.financial_metrics import (
    compute_wacc_standard,
    cost_of_equity_capm,
    dcf_schedule,
    project_fcf_years,
)


def _fmt_compact(value: float) -> str:
    v = abs(float(value))
    if v >= 1e12:
        return f"{value / 1e12:.2f} T"
    if v >= 1e9:
        return f"{value / 1e9:.2f} Bn"
    if v >= 1e6:
        return f"{value / 1e6:.2f} MM"
    return f"{value:,.0f}"


def render() -> None:
    st.markdown(
        """
        <div class="ibero-hero">
            <h1>Motor de Valoración</h1>
            <p>
                Modelo DCF y WACC con CAPM y prima de riesgo país: ajuste supuestos
                macro y financieros y observe el valor intrínseco y el precio teórico
                por acción frente al mercado.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ticker = st.session_state.get("selected_ticker")
    if not ticker:
        st.info(
            "Seleccione un ticker en **Market Monitor** y pulse "
            "**Simular Valoración Integral** para cargar el modelo."
        )
        return

    try:
        info = fetch_ticker_info(ticker)
        inputs = build_valuation_inputs(ticker, info)
    except Exception as exc:
        st.error(f"No fue posible cargar datos de valoración para **{ticker}**. {exc}")
        return

    st.caption(f"Instrumento: **{inputs.ticker}** · {inputs.country or 'N/D'} · {inputs.exchange or 'N/D'}")

    left, right = st.columns([4, 8])

    with left:
        with st.container(border=True):
            st.markdown("##### Panel de simulación")
            rf_pct = st.slider(
                "Tasa libre de riesgo Rf (%)",
                min_value=0.0,
                max_value=10.0,
                value=inputs.default_risk_free * 100.0,
                step=0.05,
                help="Bonos soberanos (p. ej. ^TNX).",
            )
            erp_pct = st.slider(
                "Prima de riesgo de mercado (Rm - Rf) (%)",
                min_value=4.0,
                max_value=9.0,
                value=DEFAULT_ERP * 100.0,
                step=0.1,
            )
            alpha_pct = st.slider(
                "Riesgo país Alpha_cr (%)",
                min_value=0.0,
                max_value=8.0,
                value=inputs.default_country_risk * 100.0,
                step=0.1,
                help="Spread adicional para mercados emergentes.",
            )
            kd_pct = st.slider(
                "Costo de la deuda Kd (%)",
                min_value=1.0,
                max_value=15.0,
                value=inputs.cost_of_debt * 100.0,
                step=0.1,
            )
            fcf_growth_pct = st.slider(
                "Crecimiento FCF explícito (%)",
                min_value=-5.0,
                max_value=15.0,
                value=DEFAULT_FCF_GROWTH * 100.0,
                step=0.5,
            )
            g_pct = st.slider(
                "Crecimiento perpetuo g (%)",
                min_value=1.0,
                max_value=5.0,
                value=DEFAULT_TERMINAL_G * 100.0,
                step=0.1,
                help="Debe ser estrictamente menor que el WACC.",
            )

    rf = rf_pct / 100.0
    erp = erp_pct / 100.0
    alpha = alpha_pct / 100.0
    kd = kd_pct / 100.0
    fcf_growth = fcf_growth_pct / 100.0

    ke = cost_of_equity_capm(rf, inputs.beta, erp, alpha)
    wacc = compute_wacc_standard(
        inputs.market_value_equity,
        inputs.total_debt,
        ke,
        kd,
        inputs.tax_rate,
    )
    wacc_pct = wacc * 100.0
    terminal_g = g_pct / 100.0
    wacc_g_invalid = wacc <= terminal_g

    fcfs = project_fcf_years(inputs.base_fcf, fcf_growth, years=5)
    if wacc_g_invalid:
        result: dict = {
            "enterprise_value": 0.0,
            "equity_value": 0.0,
            "value_per_share": 0.0,
            "valid": False,
        }
    else:
        result = dcf_schedule(
            fcfs,
            wacc,
            terminal_g,
            inputs.net_debt,
            inputs.shares_outstanding,
        )

    ev = float(result["enterprise_value"])
    vps = float(result["value_per_share"])
    market = inputs.market_price

    with right:
        with st.container(border=True):
            k1, k2, k3 = st.columns(3)
            with k1:
                st.metric("WACC", f"{wacc_pct:.2f}%", help="Kw ponderado.")
            with k2:
                st.metric(
                    "Valor intrínseco (EV)",
                    _fmt_compact(ev) if ev > 0 else "N/D",
                )
            with k3:
                delta_px = None
                if market > 0 and vps > 0:
                    delta_px = (vps - market) / market * 100.0
                st.metric(
                    "Precio teórico / mercado",
                    f"{vps:,.2f}" if vps > 0 else "N/D",
                    delta=f"{delta_px:+.1f}%" if delta_px is not None else None,
                    help=f"Mercado: {market:,.2f}",
                )

        if wacc_g_invalid:
            st.warning(
                "La tasa de crecimiento perpetuo (g) no puede ser mayor o igual al WACC. "
                "Ajuste los parámetros de simulación.",
                icon="⚠️",
            )
        elif ev <= 0 or vps <= 0 or not result.get("valid", True):
            st.warning(
                "El modelo no pudo calcular un valor positivo. Revise los flujos de caja "
                "y los supuestos de descuento."
            )
        else:
            import plotly.graph_objects as go
            from utils.styles import (
                BG_BASE,
                BG_CARD,
                GOLD_DARK,
                PLOTLY_CHART_CONFIG,
                TEXT_MAIN,
            )

            with st.container(border=True):
                labels = result["chart_labels"]
                chart_fcf = result["chart_fcf"]
                chart_pv = result["chart_pv"]
                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=labels,
                        y=chart_fcf,
                        name="FCF nominal",
                        marker_color="rgba(209, 158, 64, 0.45)",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=labels,
                        y=chart_pv,
                        name="Valor presente",
                        mode="lines+markers",
                        line=dict(color=GOLD_DARK, width=2),
                        marker=dict(size=8),
                    )
                )
                fig.update_layout(
                    title=f"Proyección DCF — {inputs.ticker}",
                    template="plotly_white",
                    height=420,
                    barmode="group",
                    paper_bgcolor=BG_CARD,
                    plot_bgcolor=BG_BASE,
                    font=dict(color=TEXT_MAIN),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    modebar=dict(
                        bgcolor="rgba(255, 255, 255, 0.96)",
                        color=TEXT_MAIN,
                        activecolor=GOLD_DARK,
                    ),
                )
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CHART_CONFIG)

            if vps > market * 1.02:
                st.success("Activo Subvalorado (Oportunidad de Compra)")
            elif vps < market * 0.98:
                st.error("Activo Sobrevalorado (Riesgo de Mercado)")
            else:
                st.warning("Precio teórico alineado con el mercado (rango de equilibrio).")

    with st.expander("Glosario académico"):
        st.markdown(
            """
            - **Rf:** tasa libre de riesgo (rendimiento de activo sin riesgo; aquí ^TNX).
            - **Rm - Rf (ERP):** prima de riesgo de mercado; compensación por volatilidad sistemática.
            - **Alpha_cr:** prima de riesgo país (EMBI/CDS o supuesto para emergentes).
            - **Beta:** sensibilidad del activo al mercado (CAPM).
            - **Ke:** costo del patrimonio = Rf + Beta × ERP + Alpha_cr.
            - **Kd:** costo de la deuda antes de impuestos; **WACC** = Ke×(E/V) + Kd×(1−T)×(D/V).
            - **FCF:** flujo de caja libre proyectado 5 años + valor terminal Gordon: TV = FCFₙ(1+g)/(WACC−g).
            - **EV:** valor de la empresa; **precio teórico** = (EV − deuda neta) / acciones.
            """
        )
