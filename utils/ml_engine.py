"""Supervised ML preparation and training for ML Predictor (no Streamlit UI)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

MODEL_LINEAR = "Regresión Lineal (Tendencias Básicas)"
MODEL_TREE = "Árbol de Decisión (Bifurcaciones Lógicas)"
MODEL_MLP = "Red Neuronal Simple (MLP - Deep Learning Introductorio)"

MIN_SUPERVISED_ROWS = 30


@dataclass(frozen=True)
class MLSupervisedSplit:
    """Chronological train/test split for next-day close prediction."""

    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    feature_names: list[str]
    train_end: pd.Timestamp
    test_start: pd.Timestamp


@dataclass(frozen=True)
class MLTrainResult:
    """Fitted model and hold-out evaluation on the test window."""

    model: Any
    y_pred: np.ndarray
    metrics: dict[str, float]


def prepare_ml_supervised_split(
    df: pd.DataFrame,
    test_ratio: float = 0.2,
) -> MLSupervisedSplit:
    """Build X (same-day features) and y (next-day close) with temporal 80/20 split.

    Args:
        df: Raw history from ``fetch_ml_historical_data``.
        test_ratio: Fraction of most recent rows reserved for test (default 20%).

    Returns:
        ``MLSupervisedSplit`` with train/test matrices.

    Raises:
        ValueError: If the frame is empty or too short after feature engineering.
    """
    if df is None or df.empty or "close" not in df.columns:
        raise ValueError("El dataset está vacío o no incluye precios de cierre.")

    data = df.sort_index().copy()
    feature_cols = ["close", "volume"]
    for optional in ("brent", "usd_cop"):
        if optional in data.columns:
            feature_cols.append(optional)

    if "volume" not in data.columns:
        data["volume"] = 0.0

    X = data[feature_cols].copy()
    y = data["close"].shift(-1)
    combined = pd.concat([X, y.rename("target")], axis=1).dropna()

    if len(combined) < MIN_SUPERVISED_ROWS:
        raise ValueError(
            f"Se requieren al menos {MIN_SUPERVISED_ROWS} observaciones válidas tras "
            "generar el target (cierre del día siguiente). Amplíe el historial de años."
        )

    split_idx = max(1, int(len(combined) * (1.0 - test_ratio)))
    if split_idx >= len(combined):
        split_idx = len(combined) - 1

    train = combined.iloc[:split_idx]
    test = combined.iloc[split_idx:]

    if test.empty or train.empty:
        raise ValueError(
            "No hay suficientes filas para separar entrenamiento y prueba. "
            "Use más años de historial."
        )

    return MLSupervisedSplit(
        X_train=train[feature_cols],
        X_test=test[feature_cols],
        y_train=train["target"],
        y_test=test["target"],
        feature_names=feature_cols,
        train_end=pd.Timestamp(train.index.max()),
        test_start=pd.Timestamp(test.index.min()),
    )


def create_regressor(model_label: str) -> Any:
    """Instantiate the sklearn estimator for the UI model choice."""
    if model_label == MODEL_LINEAR:
        return LinearRegression()
    if model_label == MODEL_TREE:
        return DecisionTreeRegressor(max_depth=5, random_state=42)
    if model_label == MODEL_MLP:
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "mlp",
                    MLPRegressor(
                        hidden_layer_sizes=(50, 25),
                        max_iter=500,
                        random_state=42,
                    ),
                ),
            ]
        )
    raise ValueError(f"Modelo no reconocido: {model_label}")


def train_and_evaluate(
    model_label: str,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> MLTrainResult:
    """Fit on the train window and score on the chronological test window."""
    model = create_regressor(model_label)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return MLTrainResult(
        model=model,
        y_pred=np.asarray(y_pred, dtype=float),
        metrics={
            "r2": float(r2_score(y_test, y_pred)),
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        },
    )


def supervised_target_dates(feature_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Map feature-day index to the calendar date of the predicted next close."""
    return pd.DatetimeIndex(
        [pd.Timestamp(d) + pd.offsets.BDay(1) for d in feature_index]
    )


def _feature_vector_from_row(
    row: pd.Series,
    feature_names: list[str],
) -> dict[str, float]:
    state: dict[str, float] = {}
    for name in feature_names:
        if name in row.index:
            val = row[name]
            state[name] = float(val) if pd.notna(val) else 0.0
        else:
            state[name] = 0.0
    return state


def iterative_forecast(
    model: Any,
    df: pd.DataFrame,
    feature_names: list[str],
    days: int,
) -> pd.Series:
    """Autoregressive multi-day forecast from the last observed row in ``df``.

    Uses same-day features to predict next-day close; feeds each prediction back
    as ``close`` for the following step while holding volume and macro at their
    last known values.
    """
    if days < 1:
        raise ValueError("El horizonte de predicción debe ser al menos 1 día.")

    data = df.sort_index()
    if data.empty:
        raise ValueError("No hay datos históricos para proyectar.")

    last_date = pd.Timestamp(data.index.max())
    state = _feature_vector_from_row(data.iloc[-1], feature_names)

    preds: list[float] = []
    dates = pd.bdate_range(start=last_date + pd.offsets.BDay(1), periods=days)

    for _ in dates:
        X_step = pd.DataFrame([state], columns=feature_names)
        next_close = float(model.predict(X_step)[0])
        preds.append(next_close)
        state["close"] = next_close

    return pd.Series(preds, index=dates, name="forecast")


def _sklearn_ctor_snippet(model_label: str) -> str:
    """Constructor expression using sklearn classes preloaded in Sandbox kernel."""
    if model_label == MODEL_LINEAR:
        return "LinearRegression()"
    if model_label == MODEL_TREE:
        return "DecisionTreeRegressor(max_depth=5, random_state=42)"
    if model_label == MODEL_MLP:
        return (
            "Pipeline([\n"
            "    ('scaler', StandardScaler()),\n"
            "    ('mlp', MLPRegressor(hidden_layer_sizes=(50, 25), max_iter=500, random_state=42)),\n"
            "])"
        )
    raise ValueError(f"Modelo no reconocido: {model_label}")


def build_sandbox_ml_export_code(
    ticker: str,
    model_label: str,
    feature_names: list[str],
    training_csv: str,
    forecast_days: int,
) -> str:
    """Generate a runnable Sandbox cell mirroring the ML Predictor experiment."""
    ctor = _sklearn_ctor_snippet(model_label)
    features_repr = repr(feature_names)
    ticker_u = (ticker or "AAPL").strip().upper()
    days = max(1, int(forecast_days))

    return f'''# --- Exportado desde ML Predictor — Universidad Iberoamericana ---
# Activo: {ticker_u} · Modelo: {model_label}
# `pd`, `np`, `data` y estimadores sklearn (LinearRegression, Pipeline, etc.) están en el kernel.

print(f"--- Réplica cuantitativa ML: {{data['ticker']}} ---")

hist = pd.read_csv(
    """{training_csv}""",
    index_col=0,
    parse_dates=True,
)
feature_names = {features_repr}
if "volume" not in hist.columns:
    hist["volume"] = 0.0

X = hist[feature_names].copy()
y = hist["close"].shift(-1)
combined = pd.concat([X, y.rename("target")], axis=1).dropna()
split_idx = max(1, int(len(combined) * 0.8))
train = combined.iloc[:split_idx]
test = combined.iloc[split_idx:]

model = {ctor}
model.fit(train[feature_names], train["target"])
test_pred = model.predict(test[feature_names])
print(f"Filas entrenamiento: {{len(train)}} · prueba: {{len(test)}}")
print(f"Último cierre real: {{hist['close'].iloc[-1]:,.2f}}")

# Proyección autorregresiva (misma lógica que ML Predictor — Paso 3)
state = hist[feature_names].iloc[-1].astype(float).to_dict()
last_date = pd.Timestamp(hist.index.max())
future_dates = pd.bdate_range(start=last_date + pd.offsets.BDay(1), periods={days})
future_prices = []
for _ in future_dates:
    row = pd.DataFrame([state], columns=feature_names)
    nxt = float(model.predict(row)[0])
    future_prices.append(nxt)
    state["close"] = nxt

print("Horizonte futuro (días hábiles):")
for d, p in zip(future_dates, future_prices, strict=True):
    print(f"  {{d.date()}} -> {{p:,.2f}}")
'''
