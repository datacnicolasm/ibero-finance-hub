"""Sidebar layout: brand, option menu, footer."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

from .styles import get_option_menu_styles

VALUATION_MENU_LABEL = "Valoración"

NAV_ROWS: tuple[tuple[str, str, str], ...] = (
    ("market", "Market Monitor", "graph-up-arrow"),
    ("valuation", VALUATION_MENU_LABEL, "calculator"),
    ("sandbox", "Sandbox Quant", "terminal"),
    ("ml", "ML Predictor", "cpu"),
)

MODULE_IDS: list[str] = [row[0] for row in NAV_ROWS]
MODULES_ORDER: list[str] = MODULE_IDS
DEFAULT_MODULE_ID = MODULE_IDS[0]

MENU_STATE_KEY = "ibero_main_nav"
CURRENT_MODULE_KEY = "current_module"
PENDING_NAV_KEY = "pending_nav_module"
_NAV_SYNC_MENU_KEY = "_ibero_sync_menu_from_module"

_ID_TO_LABEL: dict[str, str] = {row[0]: row[1] for row in NAV_ROWS}
_LABEL_TO_ID: dict[str, str] = {row[1]: row[0] for row in NAV_ROWS}

_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo-header.png"


def _menu_index_for_module(module_id: str) -> int:
    try:
        return MODULE_IDS.index(module_id)
    except ValueError:
        return 0


def _sync_menu_widget_to_module(module_id: str) -> None:
    """Align ``option_menu`` session state (call only before ``option_menu`` is drawn)."""
    if module_id in _ID_TO_LABEL:
        st.session_state[MENU_STATE_KEY] = _ID_TO_LABEL[module_id]


def apply_pending_navigation() -> None:
    """Apply deferred navigation before the sidebar ``option_menu`` is drawn."""
    pending = st.session_state.pop(PENDING_NAV_KEY, None)
    if pending and pending in _ID_TO_LABEL:
        st.session_state[CURRENT_MODULE_KEY] = pending
        _sync_menu_widget_to_module(pending)
        st.session_state[_NAV_SYNC_MENU_KEY] = True


def render_sidebar() -> str:
    """Draw sidebar, sync ``current_module`` with menu selection, rerun if changed."""
    if CURRENT_MODULE_KEY not in st.session_state:
        st.session_state[CURRENT_MODULE_KEY] = DEFAULT_MODULE_ID

    previous_module = st.session_state[CURRENT_MODULE_KEY]
    current_module = previous_module
    if current_module not in _ID_TO_LABEL:
        current_module = DEFAULT_MODULE_ID
        st.session_state[CURRENT_MODULE_KEY] = current_module

    if MENU_STATE_KEY not in st.session_state:
        _sync_menu_widget_to_module(current_module)
    elif st.session_state.get(MENU_STATE_KEY) not in _LABEL_TO_ID:
        _sync_menu_widget_to_module(current_module)
    elif st.session_state.pop(_NAV_SYNC_MENU_KEY, False):
        _sync_menu_widget_to_module(current_module)

    menu_index = _menu_index_for_module(current_module)
    labels = [row[1] for row in NAV_ROWS]
    icons = [row[2] for row in NAV_ROWS]

    with st.sidebar:
        logo_col, title_col = st.columns(
            [0.34, 0.66],
            vertical_alignment="center",
            gap="small",
        )
        with logo_col:
            if _LOGO_PATH.is_file():
                st.image(str(_LOGO_PATH), width=72)
            else:
                st.markdown(
                    '<div class="ibero-side-logo-fallback">IF</div>',
                    unsafe_allow_html=True,
                )
        with title_col:
            st.markdown(
                """
                <div class="ibero-side-title">
                  IBERO FINANCE HUB
                  <span class="sub">Corporación Universitaria Iberoamericana</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            "<div style='margin-bottom: 0.85rem; padding: 0 0.15rem;'></div>",
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
            """
            <div class="ibero-nav-footer">
              <span class="ibero-nav-footer-org">Facultad de Ciencias Empresariales</span>
              <span class="ibero-nav-footer-copy">© 2026 · Todos los derechos reservados.</span>
              <span class="ibero-nav-footer-author">Arley Nicolas Muñoz</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    active_id = _LABEL_TO_ID.get(selected_label, DEFAULT_MODULE_ID)
    st.session_state[CURRENT_MODULE_KEY] = active_id

    if active_id != previous_module:
        st.rerun()

    return active_id


def navigate_to_module(module_id: str) -> None:
    """Jump to a module; menu label sync runs on next rerun via ``apply_pending_navigation``."""
    if module_id not in _ID_TO_LABEL:
        return
    st.session_state[CURRENT_MODULE_KEY] = module_id
    st.session_state[PENDING_NAV_KEY] = module_id
