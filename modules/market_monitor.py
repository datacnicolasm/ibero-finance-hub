"""Market Monitor: terminal-style quote, chart, fundamentals."""

from __future__ import annotations

import html as html_lib
from typing import Any, Optional

import pandas as pd
import streamlit as st

from utils.data_engine import (
    TIMEFRAME_TO_HISTORY,
    fetch_ohlcv_timeframe,
    fetch_market_panel,
    get_asset_class_label,
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

_EXCHANGE_LABELS: dict[str, str] = {
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "NAS": "NASDAQ",
    "NYQ": "NYSE",
    "NYSE": "NYSE",
    "PCX": "NYSE Arca",
    "ASE": "AMEX",
    "AMX": "AMEX",
    "BUE": "B3",
    "BVMF": "B3",
    "BMV": "BMV",
    "MEX": "BMV",
    "LSE": "LSE",
    "IOB": "LSE",
    "FRA": "Frankfurt",
    "GER": "XETRA",
    "TOR": "TSX",
    "SAO": "B3",
    "SHH": "SSE",
    "SHZ": "SZSE",
    "HKG": "HKEX",
    "KOE": "KRX",
    "KSC": "KRX",
    "TAI": "TWSE",
    "TWO": "TPEx",
    "SAU": "Tadawul",
    "JKT": "IDX",
    "KLS": "Bursa Malaysia",
    "SES": "SGX",
    "BSE": "BSE",
    "NSE": "NSE",
    "BOG": "BVC",
    "SGO": "SSE Chile",
}

_COUNTRY_TO_ISO: dict[str, str] = {
    "united states": "us",
    "colombia": "co",
    "mexico": "mx",
    "canada": "ca",
    "united kingdom": "gb",
    "brazil": "br",
    "argentina": "ar",
    "chile": "cl",
    "peru": "pe",
    "germany": "de",
    "france": "fr",
    "spain": "es",
    "italy": "it",
    "netherlands": "nl",
    "switzerland": "ch",
    "japan": "jp",
    "china": "cn",
    "hong kong": "hk",
    "south korea": "kr",
    "taiwan": "tw",
    "india": "in",
    "australia": "au",
    "saudi arabia": "sa",
    "south africa": "za",
    "singapore": "sg",
    "israel": "il",
}


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


def _day_range_bounds(
    info: dict[str, Any],
    ohlcv: pd.DataFrame,
) -> tuple[Optional[float], Optional[float]]:
    lo = _info_float(info, "regularMarketDayLow", "dayLow")
    hi = _info_float(info, "regularMarketDayHigh", "dayHigh")
    if lo is not None and hi is not None:
        return lo, hi
    if not ohlcv.empty and all(c in ohlcv.columns for c in ("Low", "High")):
        last = ohlcv.iloc[-1]
        lo2 = float(last["Low"]) if pd.notna(last.get("Low")) else None
        hi2 = float(last["High"]) if pd.notna(last.get("High")) else None
        if lo2 is not None and hi2 is not None:
            return lo2, hi2
    return None, None


def _week52_bounds(info: dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
    lo = _info_float(info, "fiftyTwoWeekLow")
    hi = _info_float(info, "fiftyTwoWeekHigh")
    if lo is not None and hi is not None:
        return lo, hi
    return None, None


def _range_position_pct(
    current: Optional[float],
    min_value: Optional[float],
    max_value: Optional[float],
) -> float:
    """Normalize current price to 0–100% along [min_value, max_value]."""
    if current is None or min_value is None or max_value is None:
        return 50.0
    if max_value == min_value:
        return 50.0
    pct = ((current - min_value) / (max_value - min_value)) * 100.0
    return max(0.0, min(100.0, pct))


def _render_range_spectrum(
    title: str,
    min_value: Optional[float],
    max_value: Optional[float],
    current: Optional[float],
) -> None:
    """Spectrum bar with min/max labels and a marker for the current price."""
    if min_value is None or max_value is None:
        st.caption(f"{title}: N/D")
        return

    lo = min(min_value, max_value)
    hi = max(min_value, max_value)
    marker_pct = _range_position_pct(current, lo, hi)
    cur_label = f"{current:,.2f}" if current is not None else "N/D"

    st.html(
        f'<div class="ibero-range-spectrum">'
        f'<p class="ibero-range-title">{title}</p>'
        f'<div class="ibero-range-track-wrap">'
        f'<div class="ibero-range-track"></div>'
        f'<span class="ibero-range-marker" style="left:{marker_pct:.2f}%;" '
        f'title="Precio actual: {cur_label}">▼</span>'
        f"</div>"
        f'<div class="ibero-range-labels">'
        f'<span class="ibero-range-min"><strong>{lo:,.2f}</strong></span>'
        f'<span class="ibero-range-current">{cur_label}</span>'
        f'<span class="ibero-range-max"><strong>{hi:,.2f}</strong></span>'
        f"</div>"
        f"</div>"
    )


def _company_display_name(info: dict[str, Any], symbol: str) -> str:
    for key in ("longName", "shortName", "displayName"):
        value = info.get(key)
        if value:
            return str(value).strip()
    return symbol


def _logo_url(info: dict[str, Any]) -> Optional[str]:
    for key in ("logo_url", "companyLogoUrl", "logoUrl"):
        url = info.get(key)
        if isinstance(url, str) and url.startswith("http"):
            return url
    return None


def _exchange_label(info: dict[str, Any]) -> str:
    full = str(info.get("fullExchangeName") or "").strip()
    if full:
        lowered = full.lower()
        if "nasdaq" in lowered:
            return "NASDAQ"
        if "nyse" in lowered or "new york" in lowered:
            return "NYSE"
        if "bvc" in lowered or "colombia" in lowered:
            return "BVC"
        if "tsx" in lowered or "toronto" in lowered:
            return "TSX"
        return full.upper()

    code = str(info.get("exchange") or info.get("market") or "").strip().upper()
    if code in _EXCHANGE_LABELS:
        return _EXCHANGE_LABELS[code]
    return code or "—"


def _currency_label(info: dict[str, Any]) -> str:
    currency = str(info.get("currency") or "USD").strip().upper()
    return currency or "USD"


def _country_flag_url(info: dict[str, Any]) -> Optional[str]:
    country = str(info.get("country") or "").strip().lower()
    iso = _COUNTRY_TO_ISO.get(country)
    if not iso and len(country) == 2:
        iso = country.lower()
    if iso:
        return f"https://flagcdn.com/w20/{iso}.png"
    return None


def _render_instrument_header(info: dict[str, Any], symbol: str) -> None:
    """Yahoo-style identity block: logo, name, asset badge, exchange."""
    sym = (symbol or "").strip().upper()
    name = _company_display_name(info, sym)
    exchange = _exchange_label(info)
    currency = _currency_label(info)
    asset_label, asset_icon = get_asset_class_label(info)
    logo = _logo_url(info)
    flag_url = _country_flag_url(info)

    name_esc = html_lib.escape(name)
    sym_esc = html_lib.escape(sym)
    exchange_esc = html_lib.escape(exchange)
    currency_esc = html_lib.escape(currency)
    asset_label_esc = html_lib.escape(asset_label)
    asset_icon_esc = html_lib.escape(asset_icon)

    logo_html = ""
    if logo:
        logo_html = (
            f'<img class="ibero-instrument-logo" src="{html_lib.escape(logo, quote=True)}" '
            f'alt="{name_esc}" loading="lazy" />'
        )

    flag_html = ""
    if flag_url:
        flag_html = (
            f'<img class="ibero-instrument-flag" src="{html_lib.escape(flag_url, quote=True)}" '
            f'alt="" loading="lazy" />'
        )

    st.html(
        f'<div class="ibero-instrument-header">'
        f'<div class="ibero-instrument-row1">'
        f"{logo_html}"
        f'<div class="ibero-instrument-title">'
        f'<span class="ibero-instrument-name">{name_esc}</span>'
        f'<span class="ibero-instrument-ticker"> ({sym_esc})</span>'
        f"</div>"
        f"</div>"
        f'<div class="ibero-instrument-badge">'
        f'<span class="ibero-instrument-badge-icon" aria-hidden="true">'
        f"{asset_icon_esc}</span> "
        f'<span class="ibero-instrument-badge-label">{asset_label_esc}</span>'
        f'<span class="ibero-instrument-badge-sep" aria-hidden="true"> · </span>'
        f'<span class="ibero-instrument-badge-currency">Currency in '
        f"<strong>{currency_esc}</strong></span>"
        f'<span class="ibero-instrument-badge-sep" aria-hidden="true"> · </span>'
        f'<span class="ibero-instrument-badge-exchange">'
        f"{flag_html}"
        f'<span class="ibero-instrument-exchange">{exchange_esc}</span>'
        f"</span>"
        f"</div>"
        f"</div>"
    )


def _render_spot_price(
    last: Optional[float],
    prev: Optional[float],
    pct: Optional[float],
) -> None:
    """Terminal-style spot quote: price + inline $/pct change (no metric card)."""
    if last is None:
        st.html('<div class="ibero-spot-row"><span class="ibero-spot-price">N/A</span></div>')
        return

    change_html = ""
    if prev is not None and pct is not None:
        chg_abs = last - prev
        trend = "up" if chg_abs >= 0 else "down"
        arrow = "▲" if chg_abs >= 0 else "▼"
        change_html = (
            f'<span class="ibero-spot-change ibero-spot-change-{trend}">'
            f'<span class="ibero-spot-change-text">'
            f"{chg_abs:+.2f} ({pct:+.2f}%)"
            f"</span>"
            f'<span class="ibero-spot-arrow" aria-hidden="true">{arrow}</span>'
            f"</span>"
        )

    st.html(
        f'<div class="ibero-spot-row">'
        f'<span class="ibero-spot-price">{last:,.2f}</span>'
        f"{change_html}"
        f"</div>"
    )


def _render_company_profile_section(info: dict[str, Any]) -> None:
    st.markdown(
        '<p class="ibero-indicators-title">Perfil de la empresa</p>',
        unsafe_allow_html=True,
    )
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


def _render_general_tab(
    ticker_input: str,
    info: dict[str, Any],
    *,
    prev_c: Optional[float],
    open_p: Optional[float],
    vol: Optional[float],
    avg_vol: Optional[float],
    beta: Optional[float],
    pe: Optional[float],
    eps: Optional[float],
    tgt: Optional[float],
) -> None:
    import plotly.graph_objects as go

    left, right = st.columns([7, 3])
    ohlcv = pd.DataFrame()
    with left:
        with st.container(border=True):
            st.markdown(
                '<p class="ibero-panel-label">Temporalidad / Horizonte temporal</p>',
                unsafe_allow_html=True,
            )
            tf = st.segmented_control(
                label="Temporalidad",
                options=list(_TIMEFRAME_LABELS),
                default="6M",
                label_visibility="collapsed",
                key="market_timeframe_selector",
                width="stretch",
            )
            if not tf:
                tf = "6M"
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


def render() -> None:
    st.markdown(
        """
        <div class="ibero-hero">
            <p class="ibero-hero-heading">Market Monitor</p>
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

    with st.container(border=True):
        col_ticker, col_quote = st.columns(2, gap="medium")

        with col_ticker:
            st.markdown(
                '<p class="ibero-panel-label">Activo</p>',
                unsafe_allow_html=True,
            )
            ticker_input = st.text_input(
                "Ticker (Yahoo Finance)",
                value="AAPL",
                help="Símbolo Yahoo (ej. AAPL).",
                key="ticker_input_market",
            ).strip()

        info: Optional[dict[str, Any]] = None

        if not ticker_input:
            with col_quote:
                st.info("Ingresa un ticker para ver la cotización.")
        else:
            try:
                panel = fetch_market_panel(ticker_input)
                info = panel["info"]
                snap = panel["snapshot"]
            except Exception as exc:
                with col_quote:
                    st.error(
                        f"No fue posible obtener metadatos para **{ticker_input}**. "
                        f"Detalle: {exc}"
                    )
                info = None

        if info is not None:
            ohlcv_for_range = fetch_ohlcv_timeframe(ticker_input, "5D")
            last = snap.get("last_price")
            prev = snap.get("prev_close")
            mcap = snap.get("market_cap")

            if last is None:
                last = _info_float(info, "currentPrice", "regularMarketPrice")
            if prev is None:
                prev = _info_float(info, "previousClose", "regularMarketPreviousClose")
            if (
                not ohlcv_for_range.empty
                and "Close" in ohlcv_for_range.columns
                and last is None
            ):
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

            day_lo, day_hi = _day_range_bounds(info, ohlcv_for_range)
            w52_lo, w52_hi = _week52_bounds(info)

            with col_ticker:
                _render_instrument_header(info, ticker_input)
                _render_spot_price(last, prev, pct)

            with col_quote:
                st.markdown(
                    '<p class="ibero-panel-label">Cotización</p>',
                    unsafe_allow_html=True,
                )
                _render_range_spectrum(
                    "Rango del día",
                    day_lo,
                    day_hi,
                    last,
                )
                _render_range_spectrum(
                    "Rango de 52 semanas",
                    w52_lo,
                    w52_hi,
                    last,
                )
                st.metric(
                    "Market cap",
                    _fmt_compact_usd(mcap, is_currency=False),
                    help="Price × shares out.",
                )

    if not ticker_input or info is None:
        return

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

    _render_general_tab(
        ticker_input,
        info,
        prev_c=prev_c,
        open_p=open_p,
        vol=vol,
        avg_vol=avg_vol,
        beta=beta,
        pe=pe,
        eps=eps,
        tgt=tgt,
    )

    st.divider()
    _render_company_profile_section(info)
