"""Ibero Finance Intelligence Hub — entrypoint (config + navegación + dispatch).

Tema institucional Ibero: ``.streamlit/config.toml`` (ver también ``config.toml.example``).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from modules import market_monitor, ml_predictor, sandbox_quant, valuation
from utils.sidebar_nav import (
    CURRENT_MODULE_KEY,
    DEFAULT_MODULE_ID,
    apply_pending_navigation,
    render_sidebar,
)
from utils.styles import inject_global_styles

_APP_ROOT = Path(__file__).resolve().parent
_LOGO_FAVICON = _APP_ROOT / "assets" / "logo-header.png"

st.set_page_config(
    page_title="Ibero Finance Hub",
    page_icon=str(_LOGO_FAVICON) if _LOGO_FAVICON.is_file() else "📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    inject_global_styles()

    if CURRENT_MODULE_KEY not in st.session_state:
        st.session_state[CURRENT_MODULE_KEY] = DEFAULT_MODULE_ID

    apply_pending_navigation()
    render_sidebar()

    current_module = st.session_state[CURRENT_MODULE_KEY]
    match current_module:
        case "market":
            market_monitor.render()
        case "valuation":
            valuation.render()
        case "sandbox":
            sandbox_quant.render()
        case "ml":
            ml_predictor.render()
        case _:
            st.session_state[CURRENT_MODULE_KEY] = DEFAULT_MODULE_ID
            market_monitor.render()


if __name__ == "__main__":
    main()
