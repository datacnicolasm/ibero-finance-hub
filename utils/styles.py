"""Global theme CSS for Streamlit (institutional Ibero light identity)."""

from __future__ import annotations

import streamlit as st

# Institutional palette — Corporación Universitaria Iberoamericana
GOLD_PRIMARY = "#e8c042"
GOLD_DARK = "#d19e40"
TEXT_MAIN = "#494646"
TEXT_MUTED = "#6b6565"
BG_BASE = "#ffffff"
BG_CARD = "#ffffff"
BG_SIDEBAR = "#ececec"
BG_SIDEBAR_ELEVATED = "#ffffff"
BORDER_SUBTLE = "#e8e8e8"
BORDER_SIDEBAR = "#d8d7d7"

# Chart semantics — traditional market green/red (readable on white backgrounds)
CHART_UP = "#22ab94"
CHART_DOWN = "#f23645"

# Backward-compatible aliases for modules that imported emerald/ruby
EMERALD = CHART_UP
RUBY = CHART_DOWN

_GOLD_SELECTED_BG = "rgba(232, 192, 66, 0.2)"

# Streamlit / Plotly chart toolbar — always visible (not hover-only)
PLOTLY_CHART_CONFIG: dict[str, bool] = {
    "displaylogo": False,
    "scrollZoom": True,
    "displayModeBar": True,
}


def get_option_menu_styles() -> dict[str, dict[str, str]]:
    """Inline styles for ``streamlit_option_menu.option_menu`` (sidebar)."""
    return {
        "container": {
            "padding": "0",
            "background-color": "transparent",
        },
        "menu-title": {"display": "none"},
        "icon": {
            "color": GOLD_DARK,
            "font-size": "1.05rem",
        },
        "nav-link": {
            "font-family": "ui-sans-serif, system-ui, sans-serif",
            "font-size": "0.88rem",
            "font-weight": "500",
            "color": TEXT_MAIN,
            "padding": "0.55rem 0.65rem",
            "margin": "0.12rem 0",
            "border": "none",
            "border-radius": "9px",
        },
        "nav-link-selected": {
            "background-color": BG_SIDEBAR_ELEVATED,
            "color": TEXT_MAIN,
            "font-weight": "600",
            "border": f"1px solid {BORDER_SIDEBAR}",
            "border-radius": "9px",
            "box-shadow": f"inset 3px 0 0 0 {GOLD_DARK}, 0 1px 4px rgba(73, 70, 70, 0.06)",
        },
    }


def inject_global_styles() -> None:
    """Inject app-wide CSS aligned with institutional light theme in config.toml."""
    st.markdown(
        f"""
        <style>
            :root {{
                --ibero-gold: {GOLD_PRIMARY};
                --ibero-gold-dark: {GOLD_DARK};
                --ibero-text: {TEXT_MAIN};
                --ibero-text-muted: {TEXT_MUTED};
                --ibero-bg: {BG_BASE};
                --ibero-card: {BG_CARD};
                --ibero-border: {BORDER_SUBTLE};
                --ibero-sidebar: {BG_SIDEBAR};
                --ibero-sidebar-elevated: {BG_SIDEBAR_ELEVATED};
                --ibero-positive: {CHART_UP};
                --ibero-negative: {CHART_DOWN};
            }}
            .stApp {{
                color: var(--ibero-text);
            }}
            [data-testid="stHeader"] {{
                background-color: {BG_CARD};
                border-bottom: 1px solid var(--ibero-border);
            }}
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"] {{
                background-color: {BG_BASE};
            }}
            section[data-testid="stSidebar"],
            [data-testid="stSidebar"],
            [data-testid="stSidebar"] > div,
            [data-testid="stSidebarContent"],
            [data-testid="stSidebarUserContent"] {{
                background-color: {BG_SIDEBAR};
                padding-left: 0.4rem;
                padding-right: 0.4rem;
            }}
            [data-testid="stSidebar"] {{
                border-right: 1px solid {GOLD_DARK};
            }}
            [data-testid="stSidebar"] > div:first-child {{
                padding-top: 0.35rem;
            }}
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span {{
                color: var(--ibero-text);
            }}
            [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
            [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] span {{
                color: {TEXT_MAIN};
            }}
            [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover {{
                background-color: rgba(255, 255, 255, 0.45);
                border-radius: 6px;
            }}
            [data-testid="stSidebar"] .nav-link:hover {{
                background-color: rgba(255, 255, 255, 0.55);
            }}
            [data-testid="stSidebar"] hr {{
                border-color: {BORDER_SIDEBAR};
                margin: 0.5rem 0;
            }}
            .stButton > button[kind="primary"],
            .stButton > button[kind="secondary"],
            .stButton > button[data-testid="stBaseButton-primary"],
            .stButton > button[data-testid="stBaseButton-secondary"] {{
                background-color: {GOLD_PRIMARY};
                color: {TEXT_MAIN};
                border: 1px solid {GOLD_DARK};
                border-radius: 8px;
                font-weight: 600;
                transition:
                    background-color 0.22s ease,
                    border-color 0.22s ease,
                    color 0.22s ease,
                    box-shadow 0.22s ease,
                    transform 0.18s ease;
            }}
            .stButton > button[kind="primary"]:hover,
            .stButton > button[kind="secondary"]:hover,
            .stButton > button[data-testid="stBaseButton-primary"]:hover,
            .stButton > button[data-testid="stBaseButton-secondary"]:hover {{
                background-color: {GOLD_PRIMARY};
                color: {TEXT_MAIN};
                border-color: {GOLD_DARK};
                box-shadow: 0 3px 12px rgba(209, 158, 64, 0.28);
                transform: translateY(-1px);
            }}
            .stButton > button[kind="primary"]:active,
            .stButton > button[kind="secondary"]:active,
            .stButton > button[data-testid="stBaseButton-primary"]:active,
            .stButton > button[data-testid="stBaseButton-secondary"]:active {{
                background-color: {GOLD_DARK};
                border-color: {GOLD_DARK};
                box-shadow: 0 1px 4px rgba(209, 158, 64, 0.2);
                transform: translateY(0);
            }}
            .stButton > button[kind="primary"]:focus-visible,
            .stButton > button[kind="secondary"]:focus-visible,
            .stButton > button[data-testid="stBaseButton-primary"]:focus-visible,
            .stButton > button[data-testid="stBaseButton-secondary"]:focus-visible {{
                outline: 2px solid {GOLD_PRIMARY};
                outline-offset: 2px;
            }}
            .stTextInput input:focus,
            .stTextArea textarea:focus,
            .stNumberInput input:focus,
            [data-baseweb="select"] > div:focus-within {{
                border-color: {GOLD_PRIMARY};
                box-shadow: 0 0 0 1px {GOLD_PRIMARY};
            }}
            div[data-testid="stMetric"] {{
                background: {BG_CARD};
                border: 1px solid var(--ibero-border);
                border-radius: 10px;
                padding: 0.75rem 1rem;
            }}
            div[data-testid="stMetric"] label {{
                color: {TEXT_MAIN};
            }}
            div[data-testid="stMetric"] [data-testid="stMetricValue"],
            div[data-testid="stMetric"] [data-testid="stMetricValue"] p,
            [data-testid="stMetricValue"],
            [data-testid="stMetricValue"] p {{
                color: {TEXT_MAIN};
            }}
            [data-testid="stMetricValue"] {{
                color: {TEXT_MAIN};
            }}
            div[data-testid="stMetric"] [data-testid="stMetricDelta"],
            div[data-testid="stMetric"] [data-testid="stMetricDelta"] p {{
                color: {TEXT_MUTED};
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:first-of-type {{
                display: flex;
                align-items: center;
                padding: 0.35rem 0.35rem 0.2rem 0.35rem;
                margin-bottom: 0.15rem;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:first-of-type
            [data-testid="column"] {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-self: center;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:first-of-type
            [data-testid="column"] [data-testid="stVerticalBlock"] {{
                justify-content: center;
                flex-grow: 1;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:first-of-type
            .stElementContainer {{
                margin-bottom: 0;
                padding-top: 0;
                padding-bottom: 0;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:first-of-type
            [data-testid="stImage"] {{
                display: flex;
                align-items: center;
                justify-content: flex-start;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:first-of-type
            [data-testid="stImage"] img {{
                max-height: 76px;
                width: auto;
                max-width: 100%;
                object-fit: contain;
                display: block;
                margin: 0;
            }}
            .ibero-side-logo-fallback {{
                width: 48px;
                height: 48px;
                border-radius: 10px;
                background: linear-gradient(145deg, {GOLD_PRIMARY} 0%, {GOLD_DARK} 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 0.72rem;
                color: {TEXT_MAIN};
            }}
            .ibero-side-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-weight: 700;
                font-size: 0.72rem;
                letter-spacing: 0.14em;
                line-height: 1.25;
                color: {TEXT_MAIN};
                display: flex;
                flex-direction: column;
                justify-content: center;
                min-height: 76px;
                margin: 0;
                padding: 0;
            }}
            .ibero-side-title .sub {{
                display: block;
                font-size: 0.58rem;
                font-weight: 500;
                letter-spacing: 0.04em;
                color: {TEXT_MUTED};
                margin-top: 0.3rem;
                text-transform: none;
                line-height: 1.35;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:first-of-type
            .ibero-side-title p {{
                margin: 0;
            }}
            .ibero-nav-footer {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.68rem;
                letter-spacing: 0.03em;
                color: {TEXT_MUTED};
                text-align: center;
                padding: 1.25rem 0.5rem 0.75rem 0.5rem;
                line-height: 1.45;
                border-top: 1px solid {BORDER_SIDEBAR};
                margin-top: 0.5rem;
            }}
            .ibero-hero {{
                background: {BG_CARD};
                border: 1px solid var(--ibero-border);
                border-radius: 14px;
                padding: 1.75rem 2rem;
                margin-bottom: 1.25rem;
                box-shadow: 0 4px 18px rgba(73, 70, 70, 0.06);
            }}
            .ibero-hero h1 {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: {TEXT_MAIN};
                margin: 0 0 0.5rem 0;
                font-size: 1.85rem;
            }}
            .ibero-hero p {{
                color: {TEXT_MUTED};
                margin: 0;
                line-height: 1.55;
                max-width: 720px;
            }}
            .ibero-tm-panel {{
                background: {BG_CARD};
                border: 1px solid var(--ibero-border);
                border-radius: 12px;
                padding: 0.9rem 1.1rem 1rem 1.1rem;
                margin-bottom: 0.85rem;
            }}
            .ibero-tm-panel h4 {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.78rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {TEXT_MUTED};
                margin: 0 0 0.65rem 0;
            }}
            .ibero-tm-foot {{
                font-size: 0.72rem;
                color: {TEXT_MUTED};
                line-height: 1.45;
                padding: 0.5rem 0.25rem 0 0.25rem;
                border-top: 1px solid var(--ibero-border);
                margin-top: 0.75rem;
            }}
            .ibero-stats-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.82rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {TEXT_MAIN};
                margin: 0 0 0.65rem 0;
            }}
            div[data-testid="stDataFrame"] {{
                width: 100%;
            }}
            .ibero-cell-prompt {{
                font-family: ui-monospace, "Cascadia Code", "Source Code Pro", monospace;
                font-size: 0.85rem;
                font-weight: 600;
                color: {TEXT_MAIN};
                text-align: right;
                padding-top: 0.65rem;
                line-height: 1.2;
                white-space: nowrap;
            }}
            .ibero-cell-prompt-wrap [data-testid="stVerticalBlock"] {{
                align-items: flex-end;
            }}
            .js-plotly-plot .modebar,
            .js-plotly-plot .modebar-container,
            .js-plotly-plot .modebar-group,
            [data-testid="stPlotlyChart"] .modebar,
            [data-testid="stPlotlyChart"] .modebar-container,
            [data-testid="stPlotlyChart"] .modebar-group {{
                opacity: 1;
                visibility: visible;
                pointer-events: all;
            }}
            .js-plotly-plot .modebar--hover .modebar-group,
            [data-testid="stPlotlyChart"] .modebar--hover .modebar-group {{
                opacity: 1;
            }}
            [data-testid="stPlotlyChart"] .modebar-container {{
                background-color: rgba(255, 255, 255, 0.96);
                border: 1px solid var(--ibero-border);
                border-radius: 6px;
                padding: 3px 5px;
                box-shadow: 0 2px 8px rgba(73, 70, 70, 0.1);
            }}
            [data-testid="stPlotlyChart"] .modebar-btn {{
                color: {TEXT_MAIN};
            }}
            [data-testid="stPlotlyChart"] .modebar-btn svg path {{
                fill: {TEXT_MAIN};
            }}
            [data-testid="stPlotlyChart"] .modebar-btn:hover {{
                background-color: rgba(73, 70, 70, 0.06);
            }}
            [data-testid="stPlotlyChart"] .modebar-btn:hover svg path {{
                fill: {TEXT_MAIN};
            }}
            [data-testid="stPlotlyChart"] .modebar-btn.active {{
                background-color: rgba(232, 192, 66, 0.25);
            }}
            [data-testid="stPlotlyChart"] .modebar-btn.active svg path {{
                fill: {GOLD_DARK};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
