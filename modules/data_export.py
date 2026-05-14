"""Data Export — placeholder."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.subheader("Data Export")
    st.info(
        "Exportación estructurada a **CSV** e informes **PDF**, sin credenciales "
        "en código: uso de `st.secrets` / variables de entorno cuando aplique."
    )
