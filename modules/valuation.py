"""Motor de Valoración (DCF / múltiplos) — placeholder."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.subheader("Motor de Valoración")
    st.info(
        "Aquí se implementará el flujo de **DCF** y **múltiplos comparables** "
        "(supuestos, sensibilidades, tablas de drivers y salida a valor por acción), "
        "reutilizando funciones puras de `utils/financial_metrics.py`."
    )
