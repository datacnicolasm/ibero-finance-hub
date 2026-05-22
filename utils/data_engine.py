"""Data access and cleaning for market data via yfinance."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from curl_cffi import requests as curl_requests

logger = logging.getLogger(__name__)

import pandas as pd
import streamlit as st
import yfinance as yf

_YF_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _get_yf_session() -> curl_requests.Session:
    """curl_cffi session with browser User-Agent (required by yfinance 1.3+)."""
    session = curl_requests.Session()
    session.headers.update({"User-Agent": _YF_USER_AGENT})
    return session


def _yf_ticker(symbol: str) -> yf.Ticker:
    """Yahoo ``Ticker`` bound to the shared anti-blocking session."""
    return yf.Ticker((symbol or "").strip().upper(), session=_get_yf_session())


def _fetch_ticker_info_with_retry(symbol: str) -> dict[str, Any]:
    """Fetch ``Ticker.info`` with retries; raise if Yahoo returns empty metadata."""
    sym = (symbol or "").strip().upper()
    if not sym:
        raise ValueError("Símbolo vacío.")

    max_retries = 3
    session = _get_yf_session()
    info: dict[str, Any] = {}
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            info = yf.Ticker(sym, session=session).info or {}
            if info and "shortName" in info:
                return info
        except Exception as exc:
            last_exception = exc
            logger.warning(
                "fetch ticker info attempt %s/%s failed for %s: %s",
                attempt + 1,
                max_retries,
                sym,
                exc,
            )
        if attempt < max_retries - 1:
            time.sleep(1)

    error_msg = (
        f"Fallo al descargar metadatos de {sym}. Posible bloqueo de IP en producción."
    )
    if last_exception:
        error_msg += f" Error interno: {last_exception}"
    raise ValueError(error_msg)

NON_EQUITY_QUOTE_TYPES: frozenset[str] = frozenset(
    {
        "ETF",
        "MUTUALFUND",
        "CRYPTOCURRENCY",
        "CURRENCY",
        "FUTURE",
        "INDEX",
        "COMMODITY",
        "OPTION",
        "BOND",
    }
)

DEFAULT_RF = 0.04
DEFAULT_ERP = 0.055
DEFAULT_KD = 0.05
DEFAULT_BETA = 1.0
DEFAULT_TAX_US = 0.21
DEFAULT_TAX_CO = 0.35
DEFAULT_COUNTRY_RISK_US = 0.0
DEFAULT_COUNTRY_RISK_EM = 0.025
DEFAULT_FCF_GROWTH = 0.03
DEFAULT_TERMINAL_G = 0.025
_FX_FALLBACK_COP_PER_USD = 4000.0


@dataclass(frozen=True)
class ValuationInputs:
    """Snapshot of inputs for DCF / WACC from Yahoo Finance."""

    ticker: str
    market_value_equity: float
    total_debt: float
    beta: float
    cost_of_debt: float
    tax_rate: float
    base_fcf: float
    shares_outstanding: float
    net_debt: float
    market_price: float
    country: str
    exchange: str
    default_country_risk: float
    default_risk_free: float
    quote_currency: str
    financial_currency: str
    fx_financial_to_quote: float
    raw_base_fcf: float

TIMEFRAME_TO_HISTORY: dict[str, tuple[str, str]] = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "30m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "YTD": ("ytd", "1d"),
    "1Y": ("1y", "1d"),
    "MAX": ("max", "1mo"),
}


def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Return sorted OHLCV with numeric columns and rows without required OHLC.

    Args:
        df: Raw OHLCV dataframe from yfinance.

    Returns:
        Cleaned dataframe indexed by date ascending.
    """
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    required = ["Open", "High", "Low", "Close"]
    for col in required + (["Volume"] if "Volume" in out.columns else []):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=[c for c in required if c in out.columns])
    out = out.sort_index()
    return out


@st.cache_data(show_spinner=False)
def fetch_ohlcv(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Download historical OHLCV for a Yahoo Finance symbol.

    Args:
        ticker: Yahoo Finance ticker (e.g. ``AAPL``, ``ECOPETROL.CB``).
        period: yfinance period string (default ``6mo``).

    Returns:
        Cleaned OHLCV dataframe (possibly empty on failure).
    """
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return pd.DataFrame()
    hist = _yf_ticker(symbol).history(period=period, auto_adjust=False, actions=False)
    return clean_ohlcv(hist)


@st.cache_data(show_spinner=False)
def fetch_ohlcv_timeframe(ticker: str, timeframe: str) -> pd.DataFrame:
    """OHLCV for a UI timeframe preset (period + interval tuned for chart density).

    Args:
        ticker: Yahoo Finance symbol.
        timeframe: One of ``TIMEFRAME_TO_HISTORY`` keys (e.g. ``6M``, ``MAX``).

    Returns:
        Cleaned OHLCV dataframe; may be empty if Yahoo returns no rows.
    """
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return pd.DataFrame()
    period, interval = TIMEFRAME_TO_HISTORY.get(timeframe, ("6mo", "1d"))
    t = _yf_ticker(symbol)
    try:
        hist = t.history(
            period=period, interval=interval, auto_adjust=False, actions=False
        )
    except Exception:
        return pd.DataFrame()
    out = clean_ohlcv(hist)
    if out.empty and timeframe == "1D":
        try:
            hist = t.history(period="5d", interval="1d", auto_adjust=False, actions=False)
            out = clean_ohlcv(hist)
        except Exception:
            return pd.DataFrame()
    return out


@st.cache_data(show_spinner=False)
def fetch_ticker_info(ticker: str) -> dict[str, Any]:
    """Full ``Ticker.info`` dict (cached; fields vary by listing).

    Raises:
        ValueError: If Yahoo returns empty metadata (e.g. cloud IP block).
    """
    return _fetch_ticker_info_with_retry(ticker)


@st.cache_data(show_spinner=False)
def fetch_ticker_news(ticker: str, limit: int = 5) -> list[dict[str, Any]]:
    """Recent news items for symbol (title/link/metadata)."""
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return []
    try:
        raw = _yf_ticker(symbol).news or []
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    return raw[: max(0, int(limit))]


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_yahoo_info_value(value: Any) -> str:
    """Display a Yahoo ``info`` field as returned (no derived ratios or rescaling)."""
    if value is None:
        return "N/A"
    if isinstance(value, float) and pd.isna(value):
        return "N/A"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return f"{value:g}"
    return str(value)


# Curated keys commonly present in ``Ticker.info`` (valuation, profitability, liquidity).
_YAHOO_FINANCIAL_FIELDS: tuple[str, ...] = (
    "trailingPE",
    "forwardPE",
    "priceToBook",
    "priceToSalesTrailing12Months",
    "enterpriseToEbitda",
    "enterpriseValue",
    "marketCap",
    "pegRatio",
    "profitMargins",
    "grossMargins",
    "operatingMargins",
    "ebitdaMargins",
    "returnOnEquity",
    "returnOnAssets",
    "debtToEquity",
    "currentRatio",
    "quickRatio",
    "totalCash",
    "totalDebt",
    "totalRevenue",
    "revenuePerShare",
    "trailingEps",
    "forwardEps",
    "beta",
    "dividendYield",
    "payoutRatio",
    "bookValue",
    "fiftyTwoWeekLow",
    "fiftyTwoWeekHigh",
)


def build_yahoo_finance_metrics_df(info: dict[str, Any] | None) -> pd.DataFrame:
    """Tabular view of financial fields from Yahoo ``info`` (raw values, no transforms)."""
    data = info or {}
    rows: list[dict[str, str]] = []

    for field in _YAHOO_FINANCIAL_FIELDS:
        rows.append(
            {
                "Indicador (Yahoo Finance)": field,
                "Valor": _format_yahoo_info_value(data.get(field)),
            }
        )

    return pd.DataFrame(rows)


def build_financial_indicators_df(info: dict[str, Any] | None) -> pd.DataFrame:
    """Backward-compatible alias for ``build_yahoo_finance_metrics_df``."""
    return build_yahoo_finance_metrics_df(info)


_ASSET_CLASS_MAP: dict[str, tuple[str, str]] = {
    "EQUITY": ("Stock / Corporate Share", "🏢"),
    "MUTUALFUND": ("Mutual Fund", "📊"),
    "ETF": ("Exchange Traded Fund (ETF)", "📦"),
    "CRYPTOCURRENCY": ("Cryptocurrency / Digital Asset", "🪙"),
    "CURRENCY": ("Fiat Currency / Forex", "💱"),
    "FUTURE": ("Financial Future / Derivative", "⏳"),
    "INDEX": ("Market Index", "📈"),
    "COMMODITY": ("Physical Commodity", "🪵"),
    "BOND": ("Sovereign / Corporate Bond", "📜"),
}

_DEFAULT_ASSET_CLASS: tuple[str, str] = ("Financial Instrument", "🔍")


def _resolve_quote_type(info: dict[str, Any]) -> str:
    """Infer Yahoo ``quoteType`` with fallbacks when metadata is incomplete."""
    if not info:
        return ""
    raw = str(info.get("quoteType") or "").strip().upper()
    if raw:
        return raw
    short_name = str(info.get("shortName") or "").lower()
    currency = str(info.get("currency") or "").upper()
    if "coin" in short_name or currency == "BTC":
        return "CRYPTOCURRENCY"
    return ""


def get_asset_class_label(info: dict[str, Any] | None) -> tuple[str, str]:
    """Map yfinance metadata to an English asset-class label and icon.

    Args:
        info: ``Ticker.info`` dictionary (may be empty).

    Returns:
        Tuple of ``(asset_class_name_in_english, icon_emoji)``.
    """
    if not info:
        return _DEFAULT_ASSET_CLASS
    raw_type = _resolve_quote_type(info)
    if not raw_type and is_equity_ticker(info):
        raw_type = "EQUITY"
    return _ASSET_CLASS_MAP.get(raw_type, _DEFAULT_ASSET_CLASS)


@st.cache_data(show_spinner=False)
def fetch_market_snapshot(ticker: str) -> dict[str, Any]:
    """Load last price, previous close, market cap, and asset-class metadata.

    Args:
        ticker: Yahoo Finance ticker.

    Returns:
        Dictionary with ``last_price``, ``prev_close``, ``market_cap`` (float or
        ``None``), plus ``asset_class_label``, ``asset_class_icon``, ``quote_type_raw``.
    """
    symbol = (ticker or "").strip().upper()
    result: dict[str, Any] = {
        "last_price": None,
        "prev_close": None,
        "market_cap": None,
        "asset_class_label": _DEFAULT_ASSET_CLASS[0],
        "asset_class_icon": _DEFAULT_ASSET_CLASS[1],
        "quote_type_raw": "",
    }
    if not symbol:
        return result
    t = _yf_ticker(symbol)
    hist = t.history(period="5d", auto_adjust=False, actions=False)
    hist = clean_ohlcv(hist)
    if not hist.empty and "Close" in hist.columns:
        closes = hist["Close"].dropna()
        if len(closes) >= 1:
            result["last_price"] = _safe_float(closes.iloc[-1])
        if len(closes) >= 2:
            result["prev_close"] = _safe_float(closes.iloc[-2])
        elif len(closes) == 1:
            result["prev_close"] = result["last_price"]

    info = fetch_ticker_info(symbol)

    mc = _safe_float(info.get("marketCap"))
    if mc is None:
        try:
            fi = getattr(t, "fast_info", None)
            if fi is not None:
                mc = _safe_float(dict(fi).get("market_cap"))
        except Exception:
            mc = None
    result["market_cap"] = mc

    if result["last_price"] is None:
        lp = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        result["last_price"] = lp

    if result["prev_close"] is None:
        pc = _safe_float(
            info.get("previousClose")
            or info.get("regularMarketPreviousClose")
        )
        result["prev_close"] = pc

    label, icon = get_asset_class_label(info)
    raw_type = str(info.get("quoteType") or "").strip().upper()
    if not raw_type:
        raw_type = _resolve_quote_type(info)

    result["asset_class_label"] = label
    result["asset_class_icon"] = icon
    result["quote_type_raw"] = raw_type

    return result


def is_equity_ticker(info: dict[str, Any]) -> bool:
    """Return True if Yahoo ``info`` describes common equity (not ETF, FX, etc.).

    Args:
        info: ``Ticker.info`` dictionary.

    Returns:
        Whether valuation (DCF) applies to this instrument.
    """
    if not info:
        return False
    qt = str(info.get("quoteType") or "").strip().upper()
    if qt == "EQUITY":
        return True
    if qt in NON_EQUITY_QUOTE_TYPES:
        return False
    has_cap = _safe_float(info.get("marketCap")) is not None
    has_shares = _safe_float(info.get("sharesOutstanding")) is not None
    return has_cap or has_shares


@st.cache_data(show_spinner=False)
def fetch_risk_free_rate() -> float:
    """10Y US Treasury yield (^TNX) as decimal; fallback 4% if unavailable."""
    try:
        hist = _yf_ticker("^TNX").history(period="5d", auto_adjust=False)
        if not hist.empty and "Close" in hist.columns:
            yld = _safe_float(hist["Close"].dropna().iloc[-1])
            if yld is not None and yld > 0:
                return yld / 100.0
    except Exception:
        pass
    return DEFAULT_RF


def _quote_currency(info: dict[str, Any]) -> str:
    """Trading / quote currency (e.g. USD for NYSE ADRs)."""
    return str(info.get("currency") or "USD").strip().upper() or "USD"


def _financial_currency(info: dict[str, Any]) -> str:
    """Currency of financial statements (``financialCurrency`` on Yahoo)."""
    fin = str(info.get("financialCurrency") or "").strip().upper()
    return fin if fin else _quote_currency(info)


@st.cache_data(show_spinner=False)
def _cop_per_usd() -> float:
    """Latest USD/COP spot (COP per 1 USD) from Yahoo ``COP=X``."""
    series = _fetch_macro_close_series("COP=X", "5d")
    if not series.empty:
        rate = _safe_float(series.iloc[-1])
        if rate is not None and rate > 0:
            return rate
    return _FX_FALLBACK_COP_PER_USD


@st.cache_data(show_spinner=False)
def fx_financial_to_quote_multiplier(financial_currency: str, quote_currency: str) -> float:
    """Scale factor: amount_financial * multiplier = amount_quote."""
    fin = (financial_currency or "USD").upper()
    quote = (quote_currency or "USD").upper()
    if fin == quote:
        return 1.0
    if fin == "COP" and quote == "USD":
        cop = _cop_per_usd()
        return 1.0 / cop if cop > 0 else 1.0 / _FX_FALLBACK_COP_PER_USD
    if fin == "USD" and quote == "COP":
        return _cop_per_usd()
    pair = f"{fin}{quote}=X"
    try:
        series = _fetch_macro_close_series(pair, "5d")
        if not series.empty:
            rate = _safe_float(series.iloc[-1])
            if rate is not None and rate > 0:
                return rate
    except Exception:
        pass
    logger.warning(
        "Sin tipo de cambio %s → %s; se asume 1:1 (revise escala del DCF).",
        fin,
        quote,
    )
    return 1.0


def _to_quote_currency(amount: Optional[float], fx_mult: float) -> Optional[float]:
    if amount is None:
        return None
    return float(amount) * float(fx_mult)


def _resolve_shares_outstanding(
    info: dict[str, Any],
    *,
    price: float,
    market_cap: float,
) -> float:
    """Align share count with market cap and quote price (ADR vs local listings)."""
    shares = _safe_float(info.get("sharesOutstanding")) or 0.0
    if market_cap > 0 and price > 0:
        implied = market_cap / price
        if shares <= 0:
            return max(implied, 1.0)
        drift = abs(shares * price - market_cap) / market_cap
        if drift > 0.30:
            logger.warning(
                "sharesOutstanding inconsistente con marketCap/precio (%.0f%%); "
                "se usa implícito %.0f",
                drift * 100,
                implied,
            )
            return max(implied, 1.0)
    return max(shares, 1.0)


def _maybe_rescale_fcf(fcf: float, market_cap: float) -> float:
    """Detect FCF still in wrong units (thousands/millions) after FX conversion."""
    if market_cap <= 0 or fcf <= 0:
        return fcf
    ratio = abs(fcf) / market_cap
    if ratio <= 2.0:
        return fcf
    for divisor in (1_000.0, 1_000_000.0, 1_000_000_000.0):
        candidate = fcf / divisor
        if abs(candidate) / market_cap <= 2.0:
            logger.warning(
                "FCF/capitalización %.1fx demasiado alto; escala adicional 1/%.0f",
                ratio,
                divisor,
            )
            return candidate
    return fcf


def _fcf_raw_from_cashflow(ticker: str) -> Optional[float]:
    """Latest free cash flow in financial-statement currency (no FX)."""
    try:
        cf = _yf_ticker(ticker).cashflow
        if cf is None or cf.empty:
            return None
        for label in ("Free Cash Flow", "FreeCashFlow"):
            if label in cf.index:
                row = pd.to_numeric(cf.loc[label], errors="coerce").dropna()
                if len(row) > 0:
                    return float(row.iloc[0])
    except Exception:
        return None
    return None


def _debt_cash_from_statements(symbol: str, fx_mult: float) -> tuple[float, float]:
    """Total debt and cash from balance sheet, converted to quote currency."""
    bs, _ = _load_balance_sheet(symbol)
    debt_raw = _statement_latest_value(bs, ("Total Debt",)) or 0.0
    cash_raw = _statement_latest_value(
        bs,
        (
            "Cash And Cash Equivalents",
            "Cash Cash Equivalents And Short Term Investments",
            "Cash And Short Term Investments",
        ),
    ) or 0.0
    return debt_raw * fx_mult, cash_raw * fx_mult


def _fcf_from_cashflow(ticker: str) -> Optional[float]:
    """Backward-compatible alias; returns raw FCF (financial currency)."""
    return _fcf_raw_from_cashflow(ticker)


def _legal_tax_rate_for_jurisdiction(info: dict[str, Any]) -> float:
    """Statutory corporate tax fallback by listing country/exchange."""
    country = str(info.get("country") or "").upper()
    exchange = str(info.get("exchange") or "").upper()
    if country == "CO" or "BOG" in exchange or "BVC" in exchange:
        return DEFAULT_TAX_CO
    if country in ("US", "UNITED STATES"):
        return DEFAULT_TAX_US
    return DEFAULT_TAX_US


def _default_tax_rate(info: dict[str, Any]) -> float:
    """Use Yahoo effective rate only if within [0%, 50%]; else legal fallback."""
    for key in ("effectiveTaxRate", "taxRate"):
        t = _safe_float(info.get(key))
        if t is not None and 0.0 <= t <= 0.50:
            return t
    return _legal_tax_rate_for_jurisdiction(info)


def _default_country_risk(info: dict[str, Any]) -> float:
    country = str(info.get("country") or "").upper()
    if country in ("US", "UNITED STATES"):
        return DEFAULT_COUNTRY_RISK_US
    if country in ("CO", "COLOMBIA", "BR", "MX", "AR", "CL", "PE"):
        return DEFAULT_COUNTRY_RISK_EM
    return DEFAULT_COUNTRY_RISK_EM * 0.5


def build_valuation_inputs(ticker: str, info: Optional[dict[str, Any]] = None) -> ValuationInputs:
    """Build WACC/DCF inputs with fallbacks for missing Yahoo fields.

    Monetary fields from financial statements are converted to the quote
    currency (e.g. COP statements + USD ADR price for ``EC``).

    Args:
        ticker: Yahoo symbol.
        info: Optional pre-fetched ``info`` dict.

    Returns:
        ``ValuationInputs`` with numeric defaults where data is absent.
    """
    symbol = (ticker or "").strip().upper()
    data = info if info is not None else fetch_ticker_info(symbol)
    snap = fetch_market_snapshot(symbol)

    quote = _quote_currency(data)
    fin = _financial_currency(data)
    fx = fx_financial_to_quote_multiplier(fin, quote)

    price = _safe_float(
        snap.get("last_price")
        or data.get("currentPrice")
        or data.get("regularMarketPrice")
    ) or 0.0
    mcap = _safe_float(data.get("marketCap")) or snap.get("market_cap")
    mcap_f = float(mcap) if mcap and mcap > 0 else 0.0
    shares = _resolve_shares_outstanding(data, price=price, market_cap=mcap_f)
    e = mcap_f if mcap_f > 0 else max(price * shares, 0.0)

    debt_info = _to_quote_currency(_safe_float(data.get("totalDebt")), fx)
    cash_info = _to_quote_currency(
        _safe_float(data.get("totalCash")) or _safe_float(data.get("cash")),
        fx,
    )
    if debt_info is None and cash_info is None:
        d, cash = _debt_cash_from_statements(symbol, fx)
    else:
        d = debt_info or 0.0
        cash = cash_info or 0.0

    net_debt = d - cash
    ev_quote = _safe_float(data.get("enterpriseValue"))
    if net_debt <= 0 and ev_quote is not None and e > 0:
        net_debt = max(ev_quote - e, 0.0)

    interest = _to_quote_currency(_safe_float(data.get("interestExpense")), fx)
    if interest is not None:
        interest = abs(interest)
    kd = DEFAULT_KD
    if interest is not None and interest > 0 and d > 0:
        kd = min(max(interest / d, 0.01), 0.20)

    raw_fcf = _safe_float(data.get("freeCashflow"))
    if raw_fcf is None or raw_fcf == 0:
        raw_fcf = _fcf_raw_from_cashflow(symbol)
    if raw_fcf is None:
        ocf_raw = _safe_float(data.get("operatingCashflow"))
        capex_raw = _safe_float(data.get("capitalExpenditures"))
        if ocf_raw is not None:
            capex_abs = abs(capex_raw) if capex_raw is not None else 0.0
            raw_fcf = ocf_raw - capex_abs

    fcf = _to_quote_currency(raw_fcf, fx) if raw_fcf is not None else None
    if fcf is None or fcf <= 0:
        fcf = max(e * 0.05, 1_000_000.0)
        raw_fcf = raw_fcf if raw_fcf is not None else fcf / fx if fx else fcf
    else:
        fcf = _maybe_rescale_fcf(fcf, max(e, 1.0))

    beta = _safe_float(data.get("beta")) or DEFAULT_BETA
    rf = fetch_risk_free_rate()

    logger.debug(
        "Valoración %s | quote=%s fin=%s fx=%.6f | FCF_raw=%.4g FCF_quote=%.4g "
        "E=%.4g D=%.4g shares=%.4g price=%.4g",
        symbol,
        quote,
        fin,
        fx,
        raw_fcf or 0,
        fcf,
        e,
        d,
        shares,
        price,
    )

    return ValuationInputs(
        ticker=symbol,
        market_value_equity=max(e, 1.0),
        total_debt=max(d, 0.0),
        beta=beta,
        cost_of_debt=kd,
        tax_rate=_default_tax_rate(data),
        base_fcf=float(fcf),
        shares_outstanding=max(shares, 1.0),
        net_debt=float(net_debt),
        market_price=max(price, 0.01),
        country=str(data.get("country") or ""),
        exchange=str(data.get("exchange") or ""),
        default_country_risk=_default_country_risk(data),
        default_risk_free=rf,
        quote_currency=quote,
        financial_currency=fin,
        fx_financial_to_quote=fx,
        raw_base_fcf=float(raw_fcf or 0.0),
    )


def _format_audit_display_value(value: Any) -> str:
    """String formatter so Streamlit/Arrow can render mixed audit fields in one column."""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        v = float(value)
        if abs(v) >= 1e6:
            return f"{v:,.2f}"
        if 0 < abs(v) < 0.0001:
            return f"{v:.8g}"
        return f"{v:,.6g}"
    return str(value)


def _format_audit_money(value: Any) -> str:
    """Monetary audit fields — two decimals, quote currency."""
    if value is None:
        return "N/D"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def build_valuation_audit_payload(
    inputs: ValuationInputs,
    *,
    dcf_result: Optional[dict[str, Any]] = None,
) -> dict[str, str]:
    """Accounting + DCF closure metrics for the valuation debug table (all string values)."""
    raw: dict[str, Any] = {
        "Moneda cotización (precio)": inputs.quote_currency,
        "Moneda estados financieros": inputs.financial_currency,
        "Factor FX (fin → cotización)": inputs.fx_financial_to_quote,
        "FCF Año 0 (Base, cotización)": inputs.base_fcf,
        "FCF crudo (moneda financiera)": inputs.raw_base_fcf,
        "Acciones en circulación": inputs.shares_outstanding,
        "Deuda Total": inputs.total_debt,
        "Valor de Mercado del Patrimonio": inputs.market_value_equity,
        "Precio de mercado": inputs.market_price,
        "Deuda neta": inputs.net_debt,
    }

    tv_nominal: Any = "N/D"
    pv_terminal: Any = "N/D"
    if dcf_result and dcf_result.get("valid", True):
        tv = dcf_result.get("terminal_value_nominal")
        pv = dcf_result.get("pv_terminal")
        if tv is not None and float(tv) > 0:
            tv_nominal = float(tv)
        if pv is not None and float(pv) > 0:
            pv_terminal = float(pv)

    raw["Valor Terminal Nominal (Año 5)"] = tv_nominal
    raw["VP del Valor Terminal (Descontado)"] = pv_terminal

    formatted: dict[str, str] = {}
    money_keys = {
        "FCF Año 0 (Base, cotización)",
        "FCF crudo (moneda financiera)",
        "Acciones en circulación",
        "Deuda Total",
        "Valor de Mercado del Patrimonio",
        "Precio de mercado",
        "Deuda neta",
        "Valor Terminal Nominal (Año 5)",
        "VP del Valor Terminal (Descontado)",
    }
    for key, value in raw.items():
        if key in money_keys:
            formatted[key] = (
                _format_audit_money(value)
                if not isinstance(value, str) or value != "N/D"
                else "N/D"
            )
        else:
            formatted[key] = _format_audit_display_value(value)
    return formatted


def _statement_latest_value(df: pd.DataFrame, row_aliases: tuple[str, ...]) -> Optional[float]:
    """Return the most recent numeric value for the first matching row label."""
    if df is None or df.empty:
        return None
    index_labels = [str(i) for i in df.index]
    for alias in row_aliases:
        for label in index_labels:
            if alias.lower() in label.lower():
                series = pd.to_numeric(df.loc[label], errors="coerce").dropna()
                if len(series) > 0:
                    return float(series.iloc[0])
    return None


def _load_balance_sheet(ticker: str) -> tuple[pd.DataFrame, str]:
    """Load balance sheet; prefer quarterly with annual fallback."""
    t = _yf_ticker(ticker)
    try:
        q = t.quarterly_balance_sheet
        if q is not None and not q.empty:
            return q.copy(), "quarterly"
    except Exception:
        pass
    try:
        a = t.balance_sheet
        if a is not None and not a.empty:
            return a.copy(), "annual"
    except Exception:
        pass
    return pd.DataFrame(), "none"


def _load_income_statement(ticker: str) -> tuple[pd.DataFrame, str]:
    """Load income statement; prefer quarterly with annual fallback."""
    t = _yf_ticker(ticker)
    try:
        q = t.quarterly_financials
        if q is not None and not q.empty:
            return q.copy(), "quarterly"
    except Exception:
        pass
    try:
        a = t.financials
        if a is not None and not a.empty:
            return a.copy(), "annual"
    except Exception:
        pass
    return pd.DataFrame(), "none"


def _build_sandbox_metrics(
    info: dict[str, Any],
    balance_sheet: pd.DataFrame,
    income_statement: pd.DataFrame,
) -> dict[str, float]:
    """Consolidate scalar metrics with statement + info fallbacks."""
    tax = _default_tax_rate(info)

    total_debt = _statement_latest_value(
        balance_sheet,
        ("Total Debt", "Long Term Debt", "Short Long Term Debt"),
    )
    if total_debt is None:
        total_debt = _safe_float(info.get("totalDebt")) or 0.0

    total_cash = _statement_latest_value(
        balance_sheet,
        ("Cash", "Cash And Cash Equivalents", "Cash Cash Equivalents"),
    )
    if total_cash is None:
        total_cash = _safe_float(info.get("totalCash")) or _safe_float(info.get("cash")) or 0.0

    total_liab = _statement_latest_value(
        balance_sheet,
        ("Total Liab", "Total Liabilities Net Minority Interest", "Total Liabilities"),
    )
    if total_liab is None:
        total_liab = 0.0

    total_revenue = _statement_latest_value(
        income_statement,
        ("Total Revenue", "Revenue", "Operating Revenue"),
    )
    if total_revenue is None:
        total_revenue = _safe_float(info.get("totalRevenue")) or 0.0

    ebitda = _statement_latest_value(
        income_statement,
        ("EBITDA", "Normalized EBITDA"),
    )
    if ebitda is None:
        ebitda = _safe_float(info.get("ebitda")) or 0.0

    interest = _statement_latest_value(
        income_statement,
        ("Interest Expense", "Interest Expense Non Operating"),
    )
    if interest is None:
        interest = _safe_float(info.get("interestExpense"))
    if interest is not None:
        interest = abs(interest)
    else:
        interest = 0.0

    pretax = _statement_latest_value(
        income_statement,
        (
            "Pretax Income",
            "Income Before Tax",
            "Earnings Before Tax",
        ),
    )
    if pretax is None:
        pretax = _safe_float(info.get("pretaxIncome")) or 0.0

    return {
        "total_debt": float(total_debt),
        "total_cash": float(total_cash),
        "total_liabilities": float(total_liab),
        "total_revenue": float(total_revenue),
        "ebitda": float(ebitda),
        "interest_expense": float(interest),
        "tax_rate": float(tax),
        "pretax_income": float(pretax),
    }


@st.cache_data(show_spinner=False)
def fetch_sandbox_data(ticker_symbol: str) -> dict[str, Any]:
    """Consolidate market, statements and macro data for Sandbox Quant.

    Args:
        ticker_symbol: Yahoo Finance symbol.

    Returns:
        Structured dict with ``market``, ``market_data``, ``macro``,
        ``macro_ratios``, ``balance_sheet``, ``income_statement``, ``metrics``,
        and ``sources`` metadata.
    """
    symbol = (ticker_symbol or "").strip().upper() or "AAPL"
    info = fetch_ticker_info(symbol)
    snap = fetch_market_snapshot(symbol)

    price = _safe_float(
        snap.get("last_price")
        or info.get("currentPrice")
        or info.get("regularMarketPrice")
    ) or 0.01
    shares = _safe_float(info.get("sharesOutstanding")) or 0.0
    mcap = _safe_float(info.get("marketCap")) or snap.get("market_cap")
    if (shares is None or shares <= 0) and mcap and price > 0:
        shares = mcap / price
    shares = max(float(shares or 0.0), 1.0)

    beta = _safe_float(info.get("beta")) or DEFAULT_BETA
    market_cap = float(mcap) if mcap and mcap > 0 else price * shares

    balance_sheet, bs_period = _load_balance_sheet(symbol)
    income_statement, is_period = _load_income_statement(symbol)
    metrics = _build_sandbox_metrics(info, balance_sheet, income_statement)
    rf_decimal = fetch_risk_free_rate()

    return {
        "ticker": symbol,
        "market": {
            "last_price": float(price),
            "shares_outstanding": shares,
            "beta": float(beta),
            "market_cap": market_cap,
            "country": str(info.get("country") or ""),
            "exchange": str(info.get("exchange") or ""),
        },
        "market_data": {
            "current_price": float(price),
            "beta": float(beta),
            "market_cap": market_cap,
            "shares_outstanding": shares,
        },
        "macro": {"risk_free_rate": rf_decimal},
        "macro_ratios": {"risk_free_rate": rf_decimal * 100.0},
        "balance_sheet": balance_sheet,
        "income_statement": income_statement,
        "metrics": metrics,
        "sources": {
            "balance_sheet_period": bs_period,
            "income_statement_period": is_period,
        },
    }


@dataclass(frozen=True)
class PortfolioFetchResult:
    """Batch OHLCV download for Sandbox portfolio kernel injection."""

    series: dict[str, pd.DataFrame]
    failed: list[str]


def _normalize_portfolio_tickers(tickers_list: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in tickers_list:
        symbol = (raw or "").strip().upper()
        if symbol and symbol not in seen:
            seen.add(symbol)
            out.append(symbol)
    return out


@st.cache_data(show_spinner=False)
def _fetch_portfolio_series_cached(
    tickers: tuple[str, ...],
) -> tuple[tuple[tuple[str, pd.DataFrame], ...], tuple[str, ...]]:
    """Download ~5y OHLCV per ticker; returns serializable tuples for caching."""
    series_items: list[tuple[str, pd.DataFrame]] = []
    failed: list[str] = []
    for symbol in tickers:
        try:
            hist = _yf_ticker(symbol).history(
                period="5y",
                auto_adjust=False,
                actions=False,
            )
            df = clean_ohlcv(hist)
            if df.empty or "Close" not in df.columns:
                failed.append(symbol)
                logger.warning("Portfolio: no Close data for %s", symbol)
                continue
            series_items.append((symbol, df))
        except Exception as exc:
            failed.append(symbol)
            logger.warning("Portfolio: failed %s: %s", symbol, exc)
    return tuple(series_items), tuple(failed)


def fetch_portfolio_data(tickers_list: list[str]) -> PortfolioFetchResult:
    """Download historical OHLCV (~5 years) for multiple tickers.

    Args:
        tickers_list: Yahoo Finance symbols (any iterable of strings).

    Returns:
        ``PortfolioFetchResult`` with ``series`` mapping ticker to cleaned OHLCV
        and ``failed`` listing symbols that could not be loaded.
    """
    tickers = _normalize_portfolio_tickers(tickers_list)
    if not tickers:
        return PortfolioFetchResult(series={}, failed=[])
    series_tuple, failed_tuple = _fetch_portfolio_series_cached(tuple(tickers))
    return PortfolioFetchResult(
        series=dict(series_tuple),
        failed=list(failed_tuple),
    )


def _is_colombian_listing(symbol: str) -> bool:
    """True for Colombian listings on Yahoo (e.g. ``ECOPETROL.CB``)."""
    return (symbol or "").strip().upper().endswith(".CB")


def _fetch_macro_close_series(
    macro_ticker: str,
    period: str,
) -> pd.Series:
    """Download adjusted close for a macro Yahoo symbol; empty series on failure."""
    try:
        hist = _yf_ticker(macro_ticker).history(
            period=period,
            auto_adjust=True,
            actions=False,
        )
        if hist is None or hist.empty or "Close" not in hist.columns:
            return pd.Series(dtype=float)
        s = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        idx = pd.to_datetime(s.index)
        if getattr(idx, "tz", None) is not None:
            idx = idx.tz_convert(None)
        s.index = idx
        return s.sort_index()
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(show_spinner=False)
def fetch_ml_historical_data(
    ticker_symbol: str,
    years: int,
    include_macro: bool,
) -> pd.DataFrame:
    """Build aligned ML training features: asset close plus optional macro series.

    Args:
        ticker_symbol: Yahoo Finance symbol for the asset under study.
        years: Training history length (1–10), mapped to yfinance period.
        include_macro: If True, merge Brent oil; add USD/COP for ``.CB`` listings.

    Returns:
        DataFrame indexed by date with ``close``, ``volume``, and optional ``brent``,
        ``usd_cop``.
    """
    symbol = (ticker_symbol or "").strip().upper()
    if not symbol:
        raise ValueError("Símbolo de activo vacío.")

    yrs = max(1, min(10, int(years)))
    period = f"{yrs}y"

    max_retries = 3
    hist = None
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            hist = _yf_ticker(symbol).history(
                period=period,
                auto_adjust=True,
                actions=False,
            )
            if hist is not None and not hist.empty and "Close" in hist.columns:
                break
        except Exception as exc:
            last_exception = exc
            logger.warning(
                "fetch_ml_historical_data attempt %s/%s failed for %s: %s",
                attempt + 1,
                max_retries,
                symbol,
                exc,
            )
        if attempt < max_retries - 1:
            time.sleep(1)

    if hist is None or hist.empty or "Close" not in hist.columns:
        error_msg = (
            f"Fallo al descargar datos de {symbol} tras {max_retries} intentos. "
        )
        if last_exception:
            error_msg += f"Error interno: {last_exception}"
        raise ValueError(error_msg)

    if getattr(hist.index, "tz", None) is not None:
        hist.index = hist.index.tz_convert(None)

    idx = pd.to_datetime(hist.index)
    vol_col = (
        pd.to_numeric(hist["Volume"], errors="coerce")
        if "Volume" in hist.columns
        else pd.Series(0.0, index=idx)
    )
    out = pd.DataFrame(
        {
            "close": pd.to_numeric(hist["Close"], errors="coerce"),
            "volume": vol_col,
        },
        index=idx,
    )
    out = out.sort_index()

    if include_macro:
        brent = _fetch_macro_close_series("BZ=F", period)
        if not brent.empty:
            out = out.join(brent.rename("brent"), how="outer")

        if _is_colombian_listing(symbol):
            usd_cop = _fetch_macro_close_series("COP=X", period)
            if not usd_cop.empty:
                out = out.join(usd_cop.rename("usd_cop"), how="outer")

    out = out.sort_index().ffill().bfill()
    out = out.dropna(subset=["close"])
    if out.empty:
        raise ValueError(
            f"El dataset consolidado para {symbol} quedó vacío tras la limpieza de datos."
        )
    return out
