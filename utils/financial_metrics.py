"""Pure financial metrics: WACC building blocks, simple DCF, and ratios."""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


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
    return cost_of_equity_capm(
        risk_free_rate, equity_beta, market_risk_premium, country_risk_premium=0.0
    )


def cost_of_equity_capm(
    risk_free_rate: float,
    equity_beta: float,
    market_risk_premium: float,
    country_risk_premium: float = 0.0,
) -> float:
    """CAPM with country risk: Ke = Rf + Beta * ERP + Alpha_cr.

    Args:
        risk_free_rate: Risk-free rate (decimal).
        equity_beta: Levered beta.
        market_risk_premium: Market risk premium (Rm - Rf).
        country_risk_premium: Country risk spread (Alpha_cr).

    Returns:
        Cost of equity as a decimal.
    """
    re = (
        float(risk_free_rate)
        + float(equity_beta) * float(market_risk_premium)
        + float(country_risk_premium)
    )
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


def compute_wacc_standard(
    market_value_equity: float,
    market_value_debt: float,
    cost_of_equity_val: float,
    nominal_cost_of_debt: float,
    tax_rate: float,
) -> float:
    """WACC: Ke * (E/V) + Kd * (1 - T) * (D/V).

    Args:
        market_value_equity: Market value of equity E.
        market_value_debt: Market value of debt D.
        cost_of_equity_val: Ke (decimal).
        nominal_cost_of_debt: Kd pre-tax (decimal).
        tax_rate: Corporate tax rate T (decimal).

    Returns:
        WACC as decimal.
    """
    kd_at = cost_of_debt_after_tax(nominal_cost_of_debt, tax_rate)
    return compute_wacc(
        market_value_equity,
        market_value_debt,
        cost_of_equity_val,
        kd_at,
    )


def project_fcf_years(
    base_fcf: float,
    growth_rate: float,
    years: int = 5,
) -> list[float]:
    """Project free cash flows with constant growth from base year 0.

    Args:
        base_fcf: Last observed or normalized FCF (year 0 reference).
        growth_rate: Annual growth applied to each forward year.
        years: Number of explicit forecast years.

    Returns:
        List of FCF for years 1..years.
    """
    if years <= 0 or base_fcf <= 0:
        return []
    g = float(growth_rate)
    b = float(base_fcf)
    return [b * ((1.0 + g) ** i) for i in range(1, years + 1)]


def dcf_schedule(
    free_cash_flows: list[float],
    wacc: float,
    terminal_growth: float,
    net_debt: float,
    shares_outstanding: float,
) -> dict[str, float | list[float] | list[str]]:
    """DCF with explicit years plus Gordon terminal value; chart-friendly output.

    Args:
        free_cash_flows: FCF years 1..N.
        wacc: Discount rate (decimal).
        terminal_growth: Perpetual growth g (decimal).
        net_debt: Net debt to subtract from EV.
        shares_outstanding: Shares for per-share value.

    Returns:
        Dict with enterprise_value, equity_value, value_per_share, pv_explicit,
        pv_terminal, chart_labels, chart_nominal_fcf, chart_pv,
        terminal_value_nominal, wacc_minus_g.
    """
    core = dcf_equity_value_one_stage(
        free_cash_flows, wacc, terminal_growth, net_debt, shares_outstanding
    )
    w = float(wacc)
    g = float(terminal_growth)
    fcf = [float(x) for x in free_cash_flows]
    empty: dict[str, float | list[float] | list[str] | bool] = {
        "enterprise_value": 0.0,
        "equity_value": 0.0,
        "value_per_share": 0.0,
        "pv_explicit": 0.0,
        "pv_terminal": 0.0,
        "chart_labels": [],
        "chart_nominal_fcf": [],
        "chart_pv": [],
        "terminal_value_nominal": 0.0,
        "wacc_minus_g": 0.0,
        "valid": False,
    }
    if not fcf:
        return empty
    if w <= g:
        empty["wacc_le_g"] = True
        return empty

    pv_by_year: list[float] = []
    pv_explicit = 0.0
    for i, cf in enumerate(fcf, start=1):
        pv_i = cf / ((1.0 + w) ** i)
        pv_by_year.append(float(_q(pv_i, "0.01")))
        pv_explicit += pv_i

    fcf_n = fcf[-1]
    tv = fcf_n * (1.0 + g) / (w - g)
    n = len(fcf)
    pv_tv = tv / ((1.0 + w) ** n)

    labels = [f"Año {i}" for i in range(1, n + 1)] + ["Terminal"]
    chart_pv = pv_by_year + [float(_q(pv_tv, "0.01"))]

    return {
        "enterprise_value": core["enterprise_value"],
        "equity_value": core["equity_value"],
        "value_per_share": core["value_per_share"],
        "pv_explicit": float(_q(pv_explicit, "0.01")),
        "pv_terminal": float(_q(pv_tv, "0.01")),
        "terminal_value_nominal": float(_q(tv, "0.01")),
        "wacc_minus_g": float(_q(w - g, "0.0001")),
        "chart_labels": labels,
        "chart_nominal_fcf": fcf,
        "chart_pv": chart_pv,
        "valid": True,
    }


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
    # Gordon terminal: discount full TV back n explicit years (e.g. 5 for standard DCF).
    pv_tv = tv / ((1.0 + w) ** n)

    ev = float(_q(pv_explicit + pv_tv, "0.01"))
    eq = float(_q(ev - nd, "0.01"))
    vps = float(_q(eq / sh, "0.01"))
    out["enterprise_value"] = ev
    out["equity_value"] = eq
    out["value_per_share"] = vps
    logger.debug(
        "DCF audit | years=%d WACC=%.4f g=%.4f | PV_FCF=%.4e PV_TV=%.4e "
        "(TV_nom=%.4e @ (1+WACC)^%d) | EV=%.4e net_debt=%.4e EQ=%.4e shares=%.4e VPS=%.4f",
        n,
        w,
        g,
        pv_explicit,
        pv_tv,
        tv,
        n,
        ev,
        nd,
        eq,
        sh,
        vps,
    )
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
