"""Data access and cleaning for market data via yfinance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

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
    t = yf.Ticker(symbol)
    hist = t.history(period=period, auto_adjust=False, actions=False)
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
    t = yf.Ticker(symbol)
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
    """Full ``Ticker.info`` dict (cached; fields vary by listing)."""
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return {}
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}


@st.cache_data(show_spinner=False)
def fetch_ticker_news(ticker: str, limit: int = 5) -> list[dict[str, Any]]:
    """Recent news items for symbol (title/link/metadata)."""
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return []
    try:
        raw = yf.Ticker(symbol).news or []
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


@st.cache_data(show_spinner=False)
def fetch_market_snapshot(ticker: str) -> dict[str, Optional[float]]:
    """Load last price, previous close, and market cap for display metrics.

    Args:
        ticker: Yahoo Finance ticker.

    Returns:
        Dictionary with keys ``last_price``, ``prev_close``, ``market_cap``
        (values may be ``None`` if unavailable).
    """
    symbol = (ticker or "").strip().upper()
    result: dict[str, Optional[float]] = {
        "last_price": None,
        "prev_close": None,
        "market_cap": None,
    }
    if not symbol:
        return result
    t = yf.Ticker(symbol)
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

    info: dict[str, Any] = {}
    try:
        info = t.info or {}
    except Exception:
        info = {}

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
        hist = yf.Ticker("^TNX").history(period="5d", auto_adjust=False)
        if not hist.empty and "Close" in hist.columns:
            yld = _safe_float(hist["Close"].dropna().iloc[-1])
            if yld is not None and yld > 0:
                return yld / 100.0
    except Exception:
        pass
    return DEFAULT_RF


def _fcf_from_cashflow(ticker: str) -> Optional[float]:
    try:
        cf = yf.Ticker(ticker.strip().upper()).cashflow
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

    Args:
        ticker: Yahoo symbol.
        info: Optional pre-fetched ``info`` dict.

    Returns:
        ``ValuationInputs`` with numeric defaults where data is absent.
    """
    symbol = (ticker or "").strip().upper()
    data = info if info is not None else fetch_ticker_info(symbol)
    snap = fetch_market_snapshot(symbol)

    price = _safe_float(
        snap.get("last_price")
        or data.get("currentPrice")
        or data.get("regularMarketPrice")
    ) or 0.0
    shares = _safe_float(data.get("sharesOutstanding")) or 0.0
    mcap = _safe_float(data.get("marketCap")) or snap.get("market_cap")
    e = float(mcap) if mcap and mcap > 0 else max(price * shares, 0.0)

    d = _safe_float(data.get("totalDebt")) or 0.0
    cash = _safe_float(data.get("totalCash")) or _safe_float(data.get("cash")) or 0.0
    net_debt = d - cash
    ev = _safe_float(data.get("enterpriseValue"))
    if net_debt <= 0 and ev is not None and e > 0:
        net_debt = max(ev - e, 0.0)

    interest = _safe_float(data.get("interestExpense"))
    if interest is not None:
        interest = abs(interest)
    kd = DEFAULT_KD
    if interest is not None and interest > 0 and d > 0:
        kd = min(max(interest / d, 0.01), 0.20)

    fcf = _safe_float(data.get("freeCashflow"))
    if fcf is None or fcf == 0:
        fcf = _fcf_from_cashflow(symbol)
    if fcf is None:
        ocf = _safe_float(data.get("operatingCashflow"))
        capex = _safe_float(data.get("capitalExpenditures"))
        if ocf is not None:
            capex_abs = abs(capex) if capex is not None else 0.0
            fcf = ocf - capex_abs
    if fcf is None or fcf <= 0:
        fcf = max(e * 0.05, 1_000_000.0)

    beta = _safe_float(data.get("beta")) or DEFAULT_BETA
    rf = fetch_risk_free_rate()

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
    )
