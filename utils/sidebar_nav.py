"""Sidebar layout: brand, option menu, footer."""

from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from .styles import get_option_menu_styles

VALUATION_MENU_LABEL = "Valoración"

NAV_ROWS: tuple[tuple[str, str, str], ...] = (
    ("market", "Market Monitor", "graph-up-arrow"),
    ("valuation", VALUATION_MENU_LABEL, "calculator"),
    ("sandbox", "Sandbox Quant", "terminal"),
    ("ml", "ML Predictor", "cpu"),
    ("export", "Data Export", "download"),
)

MODULE_IDS: list[str] = [row[0] for row in NAV_ROWS]
DEFAULT_MODULE_ID = MODULE_IDS[0]

MENU_STATE_KEY = "ibero_main_nav"
CURRENT_MODULE_KEY = "current_module"
PENDING_NAV_KEY = "pending_nav_module"

_ID_TO_LABEL: dict[str, str] = {row[0]: row[1] for row in NAV_ROWS}
_LABEL_TO_ID: dict[str, str] = {row[1]: row[0] for row in NAV_ROWS}


def _menu_index_for_module(module_id: str) -> int:
    try:
        return MODULE_IDS.index(module_id)
    except ValueError:
        return 0


def apply_pending_navigation() -> None:
    """Apply deferred navigation before the sidebar ``option_menu`` is drawn."""
    pending = st.session_state.pop(PENDING_NAV_KEY, None)
    if pending and pending in _ID_TO_LABEL:
        st.session_state[CURRENT_MODULE_KEY] = pending
        st.session_state[MENU_STATE_KEY] = _ID_TO_LABEL[pending]


def render_sidebar() -> str:
    """Draw sidebar and return the active module id (synced with session state)."""
    if CURRENT_MODULE_KEY not in st.session_state:
        st.session_state[CURRENT_MODULE_KEY] = DEFAULT_MODULE_ID

    current_module = st.session_state[CURRENT_MODULE_KEY]
    if current_module not in _ID_TO_LABEL:
        current_module = DEFAULT_MODULE_ID
        st.session_state[CURRENT_MODULE_KEY] = current_module

    menu_index = _menu_index_for_module(current_module)
    labels = [row[1] for row in NAV_ROWS]
    icons = [row[2] for row in NAV_ROWS]

    st.session_state[MENU_STATE_KEY] = _ID_TO_LABEL[current_module]

    with st.sidebar:
        st.markdown(
            """
            <div class="ibero-side-brand">
              <div class="ibero-side-logo"><span>IF</span></div>
              <div class="ibero-side-title">
                IBERO FINANCE HUB
                <span class="sub">Corporación Universitaria Iberoamericana</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected_label = option_menu(
            menu_title=None,
            options=labels,
            icons=icons,
            menu_icon=None,
            default_index=menu_index,
            orientation="vertical",
            styles=get_option_menu_styles(),
            key=MENU_STATE_KEY,
        )
        st.markdown(
            '<p class="ibero-nav-footer">Docencia de Planta - Innovación 4.0</p>',
            unsafe_allow_html=True,
        )

    active_id = _LABEL_TO_ID.get(selected_label, DEFAULT_MODULE_ID)
    st.session_state[CURRENT_MODULE_KEY] = active_id
    return active_id


def navigate_to_module(module_id: str) -> None:
    """Queue navigation to a module; applied on next rerun before the sidebar menu."""
    if module_id in _ID_TO_LABEL:
        st.session_state[PENDING_NAV_KEY] = module_id
