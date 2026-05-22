"""ML Predictor — experiment configuration, training, metrics, and projection chart."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_engine import fetch_ml_historical_data
from utils.ml_engine import (
    build_sandbox_ml_export_code,
    iterative_forecast,
    prepare_ml_supervised_split,
    supervised_target_dates,
    train_and_evaluate,
)
from utils.sidebar_nav import navigate_to_module

MODEL_OPTIONS: tuple[str, ...] = (
    "Regresión Lineal (Tendencias Básicas)",
    "Árbol de Decisión (Bifurcaciones Lógicas)",
    "Red Neuronal Simple (MLP - Deep Learning Introductorio)",
)

MACRO_CHECKBOX_LABEL = (
    "Enriquecer modelo con variables macroeconómicas (TRM Dólar / Petróleo Brent)"
)

OVERFITTING_WARNING = (
    "Nota académica: Un ajuste del R² superior al 98% en datos bursátiles puede "
    "indicar sobreajuste (Overfitting). Discuta con su docente el impacto del ruido "
    "y la eficiencia del mercado."
)

HISTORICAL_CHART_DAYS = 90
SANDBOX_CELLS_KEY = "sandbox_cells"
SANDBOX_NEXT_CELL_ID_KEY = "sandbox_next_cell_id"
SANDBOX_LAST_TICKER_KEY = "sandbox_last_ticker"


def _format_price(value: float, ticker: str) -> str:
    prefix = "$"
    if ticker.upper().endswith(".CB"):
        prefix = "$"
    return f"{prefix}{value:,.2f}"


def _format_mae(value: float, ticker: str) -> str:
    return f"+/- {_format_price(value, ticker)}"


def _render_metrics_block(ticker: str) -> None:
    metrics = st.session_state.get("ml_metrics")
    if not metrics:
        return

    with st.container(border=True):
        st.markdown("##### Bloque 2: Métricas de evaluación")

        if metrics.get("r2", 0.0) > 0.98:
            st.warning(f"⚠️ {OVERFITTING_WARNING}")

        feature_names = st.session_state.get("ml_feature_names", [])
        split = st.session_state.get("ml_split_info", {})
        if feature_names and split:
            st.caption(
                f"Evaluación en el 20% más reciente del historial · "
                f"Train: {split.get('n_train', '—')} filas · "
                f"Test: {split.get('n_test', '—')} filas · "
                f"Features: {', '.join(feature_names)}"
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Coeficiente de determinación (R²)",
                f"{metrics['r2']:.4f}",
            )
            st.caption(
                "Porcentaje de la variabilidad explicada por el modelo.",
            )
        with c2:
            st.metric(
                "Error absoluto medio (MAE)",
                _format_mae(metrics["mae"], ticker),
            )
            st.caption("Error promedio en las predicciones.")
        with c3:
            st.metric(
                "Raíz del error cuadrático medio (RMSE)",
                _format_price(metrics["rmse"], ticker),
            )
            st.caption("Castiga con mayor fuerza las desviaciones grandes.")


def _build_projection_chart(ticker: str) -> None:
    df = st.session_state.get("ml_training_df")
    y_test = st.session_state.get("ml_y_test")
    y_pred = st.session_state.get("ml_y_pred")
    model = st.session_state.get("ml_fitted_model")
    feature_names = st.session_state.get("ml_feature_names", [])
    horizon = int(st.session_state.get("ml_forecast_horizon", 15))

    if df is None or model is None or not feature_names:
        return

    import plotly.graph_objects as go
    from utils.styles import (
        BG_BASE,
        BG_CARD,
        GOLD_DARK,
        GOLD_PRIMARY,
        PLOTLY_CHART_CONFIG,
        TEXT_MAIN,
        BORDER_SUBTLE,
    )

    hist = df.sort_index()
    hist_tail = hist.tail(HISTORICAL_CHART_DAYS)
    last_real_date = pd.Timestamp(hist.index.max())
    last_real_close = float(hist["close"].iloc[-1])

    try:
        future = iterative_forecast(model, hist, feature_names, horizon)
    except (ValueError, Exception) as exc:
        st.warning(f"No se pudo generar la proyección futura: {exc}")
        return

    st.session_state["ml_future_forecast"] = future

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=hist_tail.index,
            y=hist_tail["close"],
            name="Cierre histórico real",
            mode="lines",
            line=dict(color=TEXT_MAIN, width=2),
            hovertemplate="%{x|%Y-%m-%d}<br>Precio: %{y:,.2f}<extra></extra>",
        )
    )

    if y_test is not None and y_pred is not None:
        y_test_s = pd.Series(y_test) if not isinstance(y_test, pd.Series) else y_test
        pred_vals = (
            y_pred
            if hasattr(y_pred, "__len__") and not isinstance(y_pred, (str, bytes))
            else [y_pred]
        )
        test_dates = supervised_target_dates(pd.DatetimeIndex(y_test_s.index))
        fig.add_trace(
            go.Scatter(
                x=test_dates,
                y=list(pred_vals),
                name="Ajuste en prueba (20%)",
                mode="lines",
                line=dict(color=GOLD_DARK, width=2, dash="dot"),
                hovertemplate="%{x|%Y-%m-%d}<br>Estimado: %{y:,.2f}<extra></extra>",
            )
        )

    proj_x = [last_real_date, *future.index.tolist()]
    proj_y = [last_real_close, *future.tolist()]
    fig.add_trace(
        go.Scatter(
            x=proj_x,
            y=proj_y,
            name=f"Proyección futura ({horizon} días)",
            mode="lines+markers",
            line=dict(color=GOLD_PRIMARY, width=3),
            marker=dict(size=6, color=GOLD_PRIMARY),
            hovertemplate="%{x|%Y-%m-%d}<br>Proyectado: %{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"{ticker} — Histórico, validación y proyección ML",
        template="plotly_white",
        height=480,
        margin=dict(l=10, r=10, t=48, b=10),
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_BASE,
        font=dict(color=TEXT_MAIN, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
        yaxis=dict(
            side="right",
            title="Precio de cierre",
            showgrid=True,
            gridcolor="rgba(73, 70, 70, 0.1)",
            gridwidth=1,
            linecolor=BORDER_SUBTLE,
            tickfont=dict(color=TEXT_MAIN),
        ),
        xaxis=dict(
            title="Fecha",
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

    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CHART_CONFIG)


def _render_visualization_block(ticker: str) -> None:
    if not st.session_state.get("ml_metrics"):
        return

    with st.container(border=True):
        st.markdown("##### Bloque 3: Visualización de resultados")
        st.caption(
            "Gris institucional: cierre real reciente · Dorado secundario: ajuste en "
            "conjunto de prueba · Dorado Ibero: proyección autorregresiva al horizonte "
            "seleccionado."
        )
        _build_projection_chart(ticker)


def _append_sandbox_cell(code: str, ticker: str) -> None:
    cells = st.session_state.get(SANDBOX_CELLS_KEY)
    if not cells:
        cells = [
            {
                "id": 1,
                "code": "# Celda precargada\n",
                "output": "",
                "success": True,
                "executed": False,
            }
        ]
    next_id = int(st.session_state.get(SANDBOX_NEXT_CELL_ID_KEY, len(cells) + 1))
    cells.append(
        {
            "id": next_id,
            "code": code,
            "output": "",
            "success": True,
            "executed": False,
        }
    )
    st.session_state[SANDBOX_CELLS_KEY] = cells
    st.session_state[SANDBOX_NEXT_CELL_ID_KEY] = next_id + 1
    st.session_state[SANDBOX_LAST_TICKER_KEY] = ticker
    st.session_state["sandbox_ticker"] = ticker


def _render_export_bridge(ticker: str) -> None:
    if not st.session_state.get("ml_fitted_model"):
        return

    with st.container(border=True):
        st.markdown("##### Puente al Sandbox Quant")
        st.caption(
            "Exporte el mismo pipeline de entrenamiento y proyección como celda "
            "editable en el notebook cuantitativo."
        )

        if st.button(
            "🔬 Exportar Algoritmo a código en Sandbox Quant",
            type="primary",
            width="stretch",
            key="ml_export_sandbox_btn",
        ):
            df = st.session_state.get("ml_training_df")
            if df is None or df.empty:
                st.error("Entrene el modelo antes de exportar al Sandbox.")
                return

            model_label = (
                st.session_state.get("ml_model_choice_stored")
                or st.session_state.get("ml_model_choice")
                or MODEL_OPTIONS[0]
            )
            feature_names = st.session_state.get("ml_feature_names", [])
            horizon = int(st.session_state.get("ml_forecast_horizon", 15))
            training_csv = df.to_csv().replace('"""', "'''")

            code = build_sandbox_ml_export_code(
                ticker=ticker,
                model_label=model_label,
                feature_names=feature_names,
                training_csv=training_csv,
                forecast_days=horizon,
            )
            _append_sandbox_cell(code, ticker)
            navigate_to_module("sandbox")
            st.rerun()


def render() -> None:
    st.markdown(
        """
        <div class="ibero-hero">
            <p class="ibero-hero-heading">ML Predictor</p>
            <p>
                Laboratorio pedagógico de Ciencia de Datos aplicada a finanzas: configure
                el experimento, extraiga series históricas, entrene modelos de scikit-learn
                y evalúe el desempeño con métricas interpretables.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ticker = (st.session_state.get("ml_ticker") or "").strip().upper()
    if not ticker:
        st.info(
            "Seleccione un ticker en **Market Monitor** y pulse "
            "**Modelar Tendencias con ML** para cargar el activo."
        )
        return

    st.markdown(f"##### Activo en estudio: **{ticker}**")

    with st.container(border=True):
        st.markdown("##### Bloque 1: Configuración del experimento")

        model_choice = st.selectbox(
            "Modelo de aprendizaje",
            MODEL_OPTIONS,
            index=0,
            key="ml_model_choice",
        )
        train_years = st.slider(
            "Historial de entrenamiento (años)",
            min_value=1,
            max_value=10,
            value=5,
            key="ml_train_years",
        )
        st.slider(
            "Horizonte de predicción (días)",
            min_value=5,
            max_value=30,
            value=15,
            key="ml_forecast_horizon",
            help="Días hábiles proyectados de forma autorregresiva tras el entrenamiento.",
        )
        include_macro = st.checkbox(
            MACRO_CHECKBOX_LABEL,
            value=False,
            key="ml_include_macro",
        )

        st.caption(f"Modelo seleccionado: {model_choice}")

        if st.button(
            "Entrenar Modelo de ML",
            type="primary",
            width="stretch",
            key="ml_train_btn",
        ):
            try:
                with st.spinner(
                    "Extrayendo y alineando datos financieros históricos..."
                ):
                    df = fetch_ml_historical_data(
                        ticker, train_years, include_macro
                    )

                if df.empty:
                    st.error(
                        f"El dataset consolidado para **{ticker}** quedó vacío "
                        "tras la limpieza de datos."
                    )
                    st.stop()
            except ValueError as ve:
                st.error(f"❌ Error de Conexión: {ve}")
                if st.button(
                    "🔄 Limpiar Caché y Reintentar",
                    key="ml_clear_cache_retry",
                ):
                    st.cache_data.clear()
                    st.rerun()
                st.stop()
            except Exception as e:
                st.error(
                    f"❌ Ocurrió un error inesperado al procesar los datos: {e}"
                )
                st.stop()

            try:
                with st.spinner(
                    "Entrenando modelo y evaluando en conjunto de prueba..."
                ):
                    split = prepare_ml_supervised_split(df, test_ratio=0.2)
                    result = train_and_evaluate(
                        model_choice,
                        split.X_train,
                        split.X_test,
                        split.y_train,
                        split.y_test,
                    )

                st.session_state["ml_training_df"] = df
                st.session_state["ml_fitted_model"] = result.model
                st.session_state["ml_y_test"] = split.y_test
                st.session_state["ml_y_pred"] = result.y_pred
                st.session_state["ml_metrics"] = result.metrics
                st.session_state["ml_feature_names"] = split.feature_names
                st.session_state["ml_model_choice_stored"] = model_choice
                st.session_state["ml_split_info"] = {
                    "n_train": len(split.X_train),
                    "n_test": len(split.X_test),
                    "train_end": str(split.train_end.date()),
                    "test_start": str(split.test_start.date()),
                }
                st.session_state.pop("ml_future_forecast", None)

                cols = ", ".join(df.columns.tolist())
                st.success(
                    f"Modelo entrenado y evaluado. Dataset: **{len(df)}** filas "
                    f"({cols}). Proyección y gráfico disponibles abajo."
                )
                st.dataframe(df.tail(8), use_container_width=True)
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Error al entrenar el modelo: {exc}")

    _render_metrics_block(ticker)
    _render_visualization_block(ticker)
    _render_export_bridge(ticker)
