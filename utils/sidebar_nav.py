"""Sidebar layout: brand, option menu, footer."""

from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from .styles import get_option_menu_styles

NAV_ROWS: tuple[tuple[str, str, str], ...] = (
    ("market", "Market Monitor", "graph-up-arrow"),
    ("valuation", "Valoración", "calculator"),
    ("sandbox", "Sandbox Quant", "terminal"),
    ("ml", "ML Predictor", "cpu"),
    ("export", "Data Export", "download"),
)


def render_sidebar() -> str:
    """Draw sidebar and return the active module id."""
    labels = [row[1] for row in NAV_ROWS]
    icons = [row[2] for row in NAV_ROWS]
    label_to_id = {row[1]: row[0] for row in NAV_ROWS}

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
            default_index=0,
            orientation="vertical",
            styles=get_option_menu_styles(),
            key="ibero_main_nav",
        )
        st.markdown(
            '<p class="ibero-nav-footer">Docencia de Planta - Innovación 4.0</p>',
            unsafe_allow_html=True,
        )

    return label_to_id[selected_label]
