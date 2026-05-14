"""Pure financial metrics: WACC building blocks, simple DCF, and ratios."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import pandas as pd


def _q(value: float, places: str = "0.0001") -> Decimal:
    return Decimal(str(float(value))).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def cost_of_equity(
    risk_free_rate: float,
    equity_beta: float,
    market_risk_premium: float,
) -> float:
    """CAPM cost of equity: Rf + beta * ERP.

    Args:
        risk_free_rate: Risk-free rate (decimal, e.g. 0.04 for 4%).
        equity_beta: Levered equity beta.
        market_risk_premium: Expected market return minus risk-free (decimal).

    Returns:
        Cost of equity as a decimal.
    """
    re = float(risk_free_rate) + float(equity_beta) * float(market_risk_premium)
    return float(_q(re, "0.0001"))


def cost_of_debt_after_tax(nominal_cost_of_debt: float, tax_rate: float) -> float:
    """After-tax cost of debt: Rd * (1 - Tc).

    Args:
        nominal_cost_of_debt: Pre-tax cost of debt (decimal).
        tax_rate: Corporate tax rate (decimal).

    Returns:
        After-tax cost of debt as a decimal.
    """
    rd = float(nominal_cost_of_debt) * (1.0 - float(tax_rate))
    return float(_q(rd, "0.0001"))


def compute_wacc(
    market_value_equity: float,
    market_value_debt: float,
    cost_of_equity_val: float,
    cost_of_debt_after_tax_val: float,
) -> float:
    """Weighted average cost of capital (book/market value weights).

    Args:
        market_value_equity: Market value of equity (same currency as debt).
        market_value_debt: Market value of debt.
        cost_of_equity_val: Cost of equity (decimal).
        cost_of_debt_after_tax_val: After-tax cost of debt (decimal).

    Returns:
        WACC as a decimal. Returns ``0.0`` if total capital is non-positive.
    """
    e = max(float(market_value_equity), 0.0)
    d = max(float(market_value_debt), 0.0)
    v = e + d
    if v <= 0:
        return 0.0
    w_e = e / v
    w_d = d / v
    wacc = w_e * float(cost_of_equity_val) + w_d * float(cost_of_debt_after_tax_val)
    return float(_q(wacc, "0.0001"))


def dcf_equity_value_one_stage(
    free_cash_flows: list[float],
    wacc: float,
    terminal_growth: float,
    net_debt: float,
    shares_outstanding: float,
) -> dict[str, float]:
    """Two-stage DCF skeleton: explicit FCF years + Gordon growth terminal value.

    Terminal value at end of explicit period:
    TV = FCF_last * (1 + g) / (WACC - g), discounted with same WACC.

    Args:
        free_cash_flows: List of projected free cash flows (Year 1..N).
        wacc: Weighted average cost of capital (decimal).
        terminal_growth: Perpetual growth rate after explicit period (decimal).
        net_debt: Net debt subtracted from enterprise value (same units as FCF).
        shares_outstanding: Diluted shares for per-share value.

    Returns:
        Dict with ``enterprise_value``, ``equity_value``, ``value_per_share``.
        Uses ``0.0`` for invalid inputs (empty FCF, non-positive shares, WACC <= g).
    """
    fcf = [float(x) for x in free_cash_flows]
    w = float(wacc)
    g = float(terminal_growth)
    nd = float(net_debt)
    sh = float(shares_outstanding)

    out = {"enterprise_value": 0.0, "equity_value": 0.0, "value_per_share": 0.0}
    if not fcf or sh <= 0 or w <= g:
        return out

    pv_explicit = 0.0
    for i, cf in enumerate(fcf, start=1):
        pv_explicit += cf / ((1.0 + w) ** i)

    fcf_n = fcf[-1]
    tv = fcf_n * (1.0 + g) / (w - g)
    n = len(fcf)
    pv_tv = tv / ((1.0 + w) ** n)

    ev = float(_q(pv_explicit + pv_tv, "0.01"))
    eq = float(_q(ev - nd, "0.01"))
    vps = float(_q(eq / sh, "0.01"))
    out["enterprise_value"] = ev
    out["equity_value"] = eq
    out["value_per_share"] = vps
    return out


def current_ratio(
    current_assets: float,
    current_liabilities: float,
) -> Optional[float]:
    """Current ratio = current assets / current liabilities.

    Args:
        current_assets: Total current assets.
        current_liabilities: Total current liabilities.

    Returns:
        Ratio rounded to 4 decimals, or ``None`` if liabilities are zero.
    """
    cl = float(current_liabilities)
    if cl == 0:
        return None
    return float(_q(float(current_assets) / cl, "0.0001"))


def debt_to_equity(total_debt: float, total_equity: float) -> Optional[float]:
    """Debt-to-equity = total debt / total equity.

    Args:
        total_debt: Total debt.
        total_equity: Total shareholders' equity.

    Returns:
        Ratio rounded to 4 decimals, or ``None`` if equity is zero.
    """
    te = float(total_equity)
    if te == 0:
        return None
    return float(_q(float(total_debt) / te, "0.0001"))


def ratio_series_current_ratio(
    assets: pd.Series,
    liabilities: pd.Series,
) -> pd.Series:
    """Element-wise current ratio for aligned pandas series.

    Args:
        assets: Current assets series.
        liabilities: Current liabilities series (aligned index with assets).

    Returns:
        Series of ratios; NaN where liabilities are zero or misaligned.
    """
    a = pd.to_numeric(assets, errors="coerce")
    l = pd.to_numeric(liabilities, errors="coerce")
    out = a / l.replace(0, pd.NA)
    return out.astype(float)
