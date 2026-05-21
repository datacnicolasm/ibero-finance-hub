"""Market Monitor: terminal-style quote, chart, fundamentals."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import streamlit as st

from utils.data_engine import (
    TIMEFRAME_TO_HISTORY,
    fetch_market_snapshot,
    fetch_ohlcv_timeframe,
    fetch_ticker_info,
    is_equity_ticker,
)
from utils.sidebar_nav import navigate_to_module
from utils.styles import (
    BG_BASE,
    BG_CARD,
    BORDER_SUBTLE,
    CHART_DOWN,
    CHART_UP,
    GOLD_DARK,
    PLOTLY_CHART_CONFIG,
    TEXT_MAIN,
)

_TIMEFRAME_LABELS: tuple[str, ...] = ("1D", "5D", "1M", "6M", "YTD", "1Y", "MAX")


def _fmt_compact_usd(value: Optional[float], *, is_currency: bool = True) -> str:
    if value is None or (isinstance(value, float) and (pd.isna(value) or value <= 0)):
        return "N/A"
    v = float(value)
    sym = "$" if is_currency else ""
    if v >= 1e12:
        return f"{sym}{v / 1e12:.2f} T"
    if v >= 1e9:
        return f"{sym}{v / 1e9:.2f} Bn"
    if v >= 1e6:
        return f"{sym}{v / 1e6:.2f} MM"
    if v >= 1e3:
        return f"{sym}{v / 1e3:.2f} K"
    return f"{sym}{v:,.2f}" if is_currency else f"{v:,.2f}"


def _fmt_int(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/D"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "N/D"


def _info_float(info: dict[str, Any], *keys: str) -> Optional[float]:
    for k in keys:
        v = info.get(k)
        x = pd.to_numeric(v, errors="coerce")
        if x is not None and not pd.isna(x):
            return float(x)
    return None


def _day_range_str(info: dict[str, Any], ohlcv: pd.DataFrame) -> str:
    lo = _info_float(info, "regularMarketDayLow", "dayLow")
    hi = _info_float(info, "regularMarketDayHigh", "dayHigh")
    if lo is not None and hi is not None:
        return f"{lo:,.2f} – {hi:,.2f}"
    if not ohlcv.empty and all(c in ohlcv.columns for c in ("Low", "High")):
        last = ohlcv.iloc[-1]
        lo2 = float(last["Low"]) if pd.notna(last.get("Low")) else None
        hi2 = float(last["High"]) if pd.notna(last.get("High")) else None
        if lo2 is not None and hi2 is not None:
            return f"{lo2:,.2f} – {hi2:,.2f}"
    return "N/A"


def _week52_str(info: dict[str, Any]) -> str:
    lo = _info_float(info, "fiftyTwoWeekLow")
    hi = _info_float(info, "fiftyTwoWeekHigh")
    if lo is not None and hi is not None:
        return f"{lo:,.2f} – {hi:,.2f}"
    return "N/A"


def render() -> None:
    st.markdown(
        """
        <div class="ibero-hero">
            <h1>Market Monitor</h1>
            <p>
                Consola de mercado para seguimiento intradía y multi-horizonte: cotización
                en vivo, liquidez, rangos de sesión y 52 semanas, múltiplos y contexto
                fundamental — el mismo arquetipo de lectura que revisan mesas de renta
                variable, riesgo e investigación antes de ejecutar órdenes o recalibrar
                exposiciones.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    import plotly.graph_objects as go

    with st.container(border=True):
        ticker_input = st.text_input(
            "Ticker (Yahoo Finance)",
            value="AAPL",
            help="Símbolo Yahoo (ej. AAPL).",
            key="ticker_input_market",
        ).strip()

    if not ticker_input:
        st.warning("Ingresa un ticker para consultar.")
        return

    try:
        info = fetch_ticker_info(ticker_input)
        snap = fetch_market_snapshot(ticker_input)
    except Exception as exc:
        st.error(f"No fue posible obtener metadatos para **{ticker_input}**. Detalle: {exc}")
        return

    ohlcv_for_range = fetch_ohlcv_timeframe(ticker_input, "5D")
    last = snap.get("last_price")
    prev = snap.get("prev_close")
    mcap = snap.get("market_cap")

    if last is None:
        last = _info_float(info, "currentPrice", "regularMarketPrice")
    if prev is None:
        prev = _info_float(info, "previousClose", "regularMarketPreviousClose")
    if not ohlcv_for_range.empty and "Close" in ohlcv_for_range.columns and last is None:
        last = float(ohlcv_for_range["Close"].dropna().iloc[-1])
    if prev is None and not ohlcv_for_range.empty and "Close" in ohlcv_for_range.columns:
        c = ohlcv_for_range["Close"].dropna()
        if len(c) >= 2:
            prev = float(c.iloc[-2])
        else:
            prev = last

    if mcap is None:
        mcap = _info_float(info, "marketCap")

    pct: Optional[float] = None
    if last is not None and prev is not None and prev != 0:
        pct = (last - prev) / prev * 100.0

    day_rng = _day_range_str(info, ohlcv_for_range)
    w52 = _week52_str(info)

    with st.container(border=True):
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric(
                "Current price (Δ %)",
                f"{last:,.2f}" if last is not None else "N/A",
                delta=(f"{pct:+.2f}%" if pct is not None else None),
                delta_color="normal",
                help="% vs prior close.",
            )
        with k2:
            st.metric(
                "Day range (Low – High)",
                day_rng,
                help="Session low–high.",
            )
        with k3:
            st.metric(
                "52-week range",
                w52,
                help="52-week low–high.",
            )
        with k4:
            st.metric(
                "Market cap",
                _fmt_compact_usd(mcap, is_currency=False),
                help="Price × shares out.",
            )

    bridge_col1, bridge_col2, bridge_col3 = st.columns(3)
    with bridge_col1:
        if is_equity_ticker(info):
            if st.button(
                "Simular Valoración Integral",
                type="primary",
                width="stretch",
                key="btn_valuation_bridge",
            ):
                st.session_state["selected_ticker"] = ticker_input.upper()
                navigate_to_module("valuation")
                st.rerun()
        else:
            st.caption(
                "La valoración DCF solo está disponible para **acciones** (equity)."
            )
    with bridge_col2:
        if st.button(
            "Abrir en Sandbox Quant",
            type="primary",
            width="stretch",
            key="btn_sandbox_bridge",
        ):
            st.session_state["sandbox_ticker"] = ticker_input.upper()
            navigate_to_module("sandbox")
            st.rerun()
    with bridge_col3:
        if st.button(
            "Modelar Tendencias con ML",
            type="primary",
            width="stretch",
            key="btn_ml_bridge",
        ):
            st.session_state["ml_ticker"] = ticker_input.upper()
            navigate_to_module("ml")
            st.rerun()

    prev_c = _info_float(info, "previousClose", "regularMarketPreviousClose")
    open_p = _info_float(info, "open", "regularMarketOpen")
    vol = _info_float(info, "volume", "regularMarketVolume")
    avg_vol = _info_float(
        info, "averageVolume10days", "averageVolume", "averageDailyVolume10Day"
    )
    beta = _info_float(info, "beta")
    pe = _info_float(info, "trailingPE", "forwardPE")
    eps = _info_float(info, "trailingEps", "epsTrailingTwelveMonths")
    tgt = _info_float(info, "targetMeanPrice", "targetMedianPrice")

    left, right = st.columns([7, 3])
    ohlcv = pd.DataFrame()
    with left:
        with st.container(border=True):
            tf = st.selectbox(
                "Temporalidad",
                options=list(_TIMEFRAME_LABELS),
                index=3,
                key="market_timeframe",
            )
            iv = TIMEFRAME_TO_HISTORY.get(tf, ("6mo", "1d"))[1]
            st.caption(f"Intervalo Yahoo: `{iv}` · fuente: Yahoo Finance")

            ohlcv = fetch_ohlcv_timeframe(ticker_input, tf)
            if ohlcv.empty:
                st.error(
                    "No hay velas para este rango. Prueba otra temporalidad o verifica el ticker."
                )
            else:
                fig = go.Figure(
                    data=[
                        go.Candlestick(
                            x=ohlcv.index,
                            open=ohlcv["Open"],
                            high=ohlcv["High"],
                            low=ohlcv["Low"],
                            close=ohlcv["Close"],
                            increasing_line_color=CHART_UP,
                            increasing_fillcolor=CHART_UP,
                            decreasing_line_color=CHART_DOWN,
                            decreasing_fillcolor=CHART_DOWN,
                            name=ticker_input.upper(),
                        )
                    ]
                )
                fig.update_layout(
                    title=f"{ticker_input.upper()} — {tf}",
                    template="plotly_white",
                    height=480,
                    margin=dict(l=10, r=10, t=44, b=10),
                    paper_bgcolor=BG_CARD,
                    plot_bgcolor=BG_BASE,
                    xaxis_rangeslider_visible=False,
                    font=dict(color=TEXT_MAIN, size=12),
                    yaxis=dict(
                        side="right",
                        showgrid=True,
                        gridcolor="rgba(73, 70, 70, 0.1)",
                        gridwidth=1,
                        linecolor=BORDER_SUBTLE,
                        tickfont=dict(color=TEXT_MAIN),
                    ),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(73, 70, 70, 0.08)",
                        gridwidth=1,
                        linecolor=BORDER_SUBTLE,
                        tickfont=dict(color=TEXT_MAIN),
                    ),
                    modebar=dict(
                        bgcolor="rgba(255, 255, 255, 0.96)",
                        color=TEXT_MAIN,
                        activecolor=GOLD_DARK,
                    ),
                )
                st.plotly_chart(fig, width="stretch", config=PLOTLY_CHART_CONFIG)

    with right:
        with st.container(border=True):
            st.markdown(
                '<p class="ibero-stats-title">Estadísticas clave</p>',
                unsafe_allow_html=True,
            )
            if vol is None and not ohlcv.empty and "Volume" in ohlcv.columns:
                vser = ohlcv["Volume"].dropna()
                if len(vser) > 0:
                    vol = float(vser.iloc[-1])
            stat_rows = [
                ("Cierre anterior", f"{prev_c:,.2f}" if prev_c is not None else "N/D"),
                ("Apertura", f"{open_p:,.2f}" if open_p is not None else "N/D"),
                ("Volumen", _fmt_compact_usd(vol, is_currency=False)),
                ("Vol. promedio", _fmt_compact_usd(avg_vol, is_currency=False)),
                ("Beta (5Y mens.)", f"{beta:.2f}" if beta is not None else "N/D"),
                ("PER (TTM)", f"{pe:.2f}" if pe is not None else "N/D"),
                ("BPA (TTM)", f"{eps:,.2f}" if eps is not None else "N/D"),
                ("Objetivo 1Y (est.)", f"{tgt:,.2f}" if tgt is not None else "N/D"),
            ]
            stats_df = pd.DataFrame(stat_rows, columns=["Métrica", "Valor"])
            styled = stats_df.style.set_properties(
                subset=["Valor"],
                **{
                    "text-align": "right",
                    "font-variant-numeric": "tabular-nums",
                    "white-space": "nowrap",
                },
            ).set_properties(
                subset=["Métrica"],
                **{"font-weight": "500"},
            )
            st.dataframe(
                styled,
                width="stretch",
                hide_index=True,
                column_config={
                    "Métrica": st.column_config.TextColumn(
                        "Métrica",
                        width="medium",
                    ),
                    "Valor": st.column_config.TextColumn("Valor"),
                },
            )

    st.subheader("Resumen de empresa")
    with st.container(border=True):
        sector = info.get("sector") or "N/D"
        industry = info.get("industry") or "N/D"
        empl = info.get("fullTimeEmployees")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Sector**  \n{sector}")
        with c2:
            st.markdown(f"**Industria**  \n{industry}")
        with c3:
            st.markdown(f"**Empleados (FT)**  \n{_fmt_int(empl)}")
        summary = info.get("longBusinessSummary")
        if summary:
            st.markdown("---")
            st.markdown(str(summary))
        else:
            st.info("No hay resumen largo disponible para este listado.")

    st.markdown(
        """
        <div class="ibero-tm-foot">
        <strong>Nota docente:</strong> precios, rangos, volumen, beta y PER/BPA
        conectan con <em>Mercado de Capitales</em> (formación de precios, riesgo-rendimiento,
        eficiencia informacional) y con <em>Análisis Financiero</em> (múltiplos cotizados y
        contexto del negocio para valoración relativa y absoluta).
        </div>
        """,
        unsafe_allow_html=True,
    )
