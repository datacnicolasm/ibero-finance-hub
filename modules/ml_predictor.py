"""ML Predictor — placeholder."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.subheader("ML Predictor")
    st.info(
        "Plantillas con **scikit-learn** y **statsmodels** para modelos explicables "
        "(regresión, árboles) sobre series financieras, con imputación y manejo "
        "explícito de **NaN** antes de entrenar."
    )
