"""Safe-ish execution of student Python scripts in Sandbox Quant."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from io import StringIO
from typing import Any

import numpy as np
import pandas as pd

_SAFE_BUILTINS: dict[str, Any] = {
    "print": print,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "sorted": sorted,
    "reversed": reversed,
    "any": any,
    "all": all,
    "isinstance": isinstance,
    "type": type,
    "Exception": Exception,
    "ValueError": ValueError,
    "KeyError": KeyError,
    "ZeroDivisionError": ZeroDivisionError,
}


@dataclass(frozen=True)
class SandboxRunResult:
    """Outcome of a single sandbox script run."""

    success: bool
    stdout: str
    error_message: str | None = None


def _make_local_context(sandbox_data: dict[str, Any]) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "data": sandbox_data,
        "pd": pd,
        "np": np,
    }
    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.neural_network import MLPRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.tree import DecisionTreeRegressor

        ctx.update(
            {
                "LinearRegression": LinearRegression,
                "DecisionTreeRegressor": DecisionTreeRegressor,
                "MLPRegressor": MLPRegressor,
                "Pipeline": Pipeline,
                "StandardScaler": StandardScaler,
            }
        )
    except ImportError:
        pass
    return ctx


def _exec_cell_code(
    user_code: str,
    local_context: dict[str, Any],
) -> SandboxRunResult:
    """Execute one cell in an existing shared kernel context."""
    code = (user_code or "").strip()
    if not code:
        return SandboxRunResult(
            success=False,
            stdout="",
            error_message="El script está vacío. Escribe código antes de ejecutar.",
        )

    old_stdout = sys.stdout
    redirected = StringIO()
    sys.stdout = redirected

    try:
        exec(
            code,
            {"__builtins__": _SAFE_BUILTINS},
            local_context,
        )
        return SandboxRunResult(success=True, stdout=redirected.getvalue())
    except Exception as exc:
        return SandboxRunResult(
            success=False,
            stdout=redirected.getvalue(),
            error_message=str(exc),
        )
    finally:
        sys.stdout = old_stdout


def run_sandbox_script(user_code: str, sandbox_data: dict[str, Any]) -> SandboxRunResult:
    """Execute student code with preloaded ``data``, ``pd``, and ``np``.

    Args:
        user_code: Python source typed by the user.
        sandbox_data: Full payload from ``fetch_sandbox_data``.

    Returns:
        ``SandboxRunResult`` with captured stdout or error message.
    """
    return _exec_cell_code(user_code, _make_local_context(sandbox_data))


def run_sandbox_cells_through(
    cell_codes: list[str],
    end_index: int,
    sandbox_data: dict[str, Any],
) -> list[SandboxRunResult]:
    """Run cells 0 through ``end_index`` in one shared kernel (Jupyter-style).

    Stops at the first failing cell; later cells are not executed.

    Args:
        cell_codes: Source for each notebook cell.
        end_index: Last cell index to run (inclusive).
        sandbox_data: Full payload from ``fetch_sandbox_data``.

    Returns:
        One ``SandboxRunResult`` per executed cell (length <= end_index + 1).
    """
    if end_index < 0:
        return []

    local_context = _make_local_context(sandbox_data)
    results: list[SandboxRunResult] = []

    for i in range(end_index + 1):
        result = _exec_cell_code(cell_codes[i], local_context)
        results.append(result)
        if not result.success:
            break

    return results
