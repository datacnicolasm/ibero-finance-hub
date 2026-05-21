"""Ibero Finance Intelligence Hub — entrypoint (config + navegación + dispatch).

Para tema oscuro nativo: copia ``.streamlit/config.toml.example`` a ``.streamlit/config.toml``.
"""

from __future__ import annotations

import streamlit as st

from modules import data_export, market_monitor, ml_predictor, sandbox_quant, valuation
from utils.sidebar_nav import apply_pending_navigation, render_sidebar
from utils.styles import inject_global_styles

st.set_page_config(
    page_title="Ibero Finance Intelligence Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    inject_global_styles()
    apply_pending_navigation()
    active = render_sidebar()
    match active:
        case "market":
            market_monitor.render()
        case "valuation":
            valuation.render()
        case "sandbox":
            sandbox_quant.render()
        case "ml":
            ml_predictor.render()
        case "export":
            data_export.render()
        case _:
            market_monitor.render()


if __name__ == "__main__":
    main()
