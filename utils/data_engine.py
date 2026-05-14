"""Data access and cleaning for market data via yfinance."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

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
