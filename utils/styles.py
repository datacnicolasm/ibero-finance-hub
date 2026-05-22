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
BG_INPUT = "#f2f1f1"

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
            /* Form controls — visible gold border + soft gray fill (not white-on-white) */
            [data-testid="stTextInput"] input,
            [data-testid="stTextArea"] textarea,
            [data-testid="stNumberInput"] input,
            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input {{
                background-color: {BG_INPUT} !important;
                border: 1.5px solid {GOLD_DARK} !important;
                border-radius: 8px;
                color: {TEXT_MAIN};
            }}
            [data-testid="stSelectbox"] [data-baseweb="select"] > div,
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
            [data-testid="stMain"] [data-baseweb="select"] > div,
            [data-baseweb="select"] > div {{
                background-color: {BG_INPUT} !important;
                border: 1.5px solid {GOLD_DARK} !important;
                border-radius: 8px;
                color: {TEXT_MAIN};
            }}
            [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
                background-color: {BG_INPUT} !important;
                border: 1.5px solid {GOLD_DARK} !important;
                border-radius: 8px;
            }}
            [data-testid="stTextInput"] input:hover,
            [data-testid="stTextArea"] textarea:hover,
            [data-testid="stNumberInput"] input:hover,
            .stTextInput input:hover,
            .stTextArea textarea:hover,
            .stNumberInput input:hover,
            [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
            [data-baseweb="select"] > div:hover {{
                border-color: {GOLD_PRIMARY};
                background-color: {BG_INPUT};
            }}
            .stTextInput input:focus,
            .stTextArea textarea:focus,
            .stNumberInput input:focus,
            [data-testid="stTextInput"] input:focus,
            [data-testid="stTextArea"] textarea:focus,
            [data-testid="stNumberInput"] input:focus,
            [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
            [data-baseweb="select"] > div:focus-within {{
                border-color: {GOLD_PRIMARY};
                background-color: {BG_INPUT};
                box-shadow: 0 0 0 2px rgba(232, 192, 66, 0.35);
                outline: none;
            }}
            div[data-testid="stMetric"] {{
                background: {BG_CARD};
                border: 1px solid var(--ibero-border);
                border-radius: 10px;
                padding: 0.75rem 1rem;
                margin-bottom: 0.25rem;
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
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0.28rem;
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.72rem;
                letter-spacing: 0.02em;
                color: {TEXT_MUTED};
                text-align: center;
                padding: 1rem 0.5rem 0.75rem 0.5rem;
                line-height: 1.45;
                border-top: 1px solid {BORDER_SIDEBAR};
                margin-top: 0.5rem;
            }}
            .ibero-nav-footer span {{
                display: block;
                width: 100%;
            }}
            .ibero-nav-footer-org {{
                font-size: 0.74rem;
                font-weight: 500;
                color: {TEXT_MAIN};
            }}
            .ibero-nav-footer-copy {{
                font-size: 0.68rem;
                color: {TEXT_MUTED};
            }}
            .ibero-nav-footer-author {{
                font-size: 0.72rem;
                font-weight: 600;
                color: {TEXT_MAIN};
                margin-top: 0.2rem;
                letter-spacing: 0.03em;
            }}
            .ibero-hero {{
                background: {BG_CARD};
                border: 1px solid var(--ibero-border);
                border-radius: 14px;
                padding: 1.75rem 2rem;
                margin-bottom: 1.25rem;
                box-shadow: 0 4px 18px rgba(73, 70, 70, 0.06);
            }}
            .ibero-hero h1,
            .ibero-hero-heading {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: {TEXT_MAIN};
                margin: 0 0 0.5rem 0;
                font-size: 1.85rem;
            }}
            .ibero-hero-heading {{
                display: block;
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
            .ibero-stats-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.82rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {TEXT_MAIN};
                margin: 0 0 0.65rem 0;
            }}
            .ibero-indicators-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 1.05rem;
                font-weight: 600;
                color: {TEXT_MAIN};
                margin: 0 0 0.65rem 0;
                letter-spacing: -0.01em;
            }}
            [data-testid="stMain"] [data-testid="stTabs"] {{
                margin-top: 0.35rem;
            }}
            [data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab-list"] {{
                gap: 0.5rem;
                padding: 0.15rem 0 0.35rem;
                margin-bottom: 0;
                background: transparent;
                border: none;
            }}
            [data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab-border"] {{
                display: none;
            }}
            [data-testid="stMain"] [data-testid="stTabs"] button[data-baseweb="tab"],
            [data-testid="stMain"] [data-testid="stTabs"] [data-testid="stTab"] {{
                padding: 0.55rem 1.2rem !important;
                margin: 0 !important;
                min-height: 2.5rem;
                border: 1px solid {BORDER_SIDEBAR} !important;
                border-radius: 8px !important;
                background-color: {BG_SIDEBAR} !important;
                color: {TEXT_MUTED} !important;
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.9rem !important;
                font-weight: 500 !important;
                line-height: 1.25 !important;
                transition:
                    background-color 0.18s ease,
                    border-color 0.18s ease,
                    color 0.18s ease;
            }}
            [data-testid="stMain"] [data-testid="stTabs"] button[data-baseweb="tab"]:hover:not([aria-selected="true"]),
            [data-testid="stMain"] [data-testid="stTabs"] [data-testid="stTab"]:hover:not([aria-selected="true"]) {{
                background-color: {BG_INPUT} !important;
                color: {TEXT_MAIN} !important;
                border-color: {GOLD_DARK} !important;
            }}
            [data-testid="stMain"] [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
            [data-testid="stMain"] [data-testid="stTabs"] button[aria-selected="true"][data-testid="stTab"] {{
                background-color: {BG_BASE} !important;
                color: {TEXT_MAIN} !important;
                font-weight: 600 !important;
                border-color: {GOLD_DARK} !important;
                box-shadow: inset 0 3px 0 0 {GOLD_DARK};
            }}
            [data-testid="stMain"] [data-testid="stTabs"] [role="tabpanel"],
            [data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab-panel"],
            [data-testid="stMain"] [data-testid="stTabs"] div[id^="tabs-"][id$="-tabpanel"] {{
                padding: 0.5rem 0 0;
                margin-top: 0.25rem;
                background: transparent;
                border: none;
            }}
            .ibero-panel-label {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.78rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {TEXT_MUTED};
                margin: 0 0 0.35rem 0;
            }}
            .ibero-instrument-header {{
                margin: 0.65rem 0 0.15rem 0;
                padding: 0.15rem 0 0.35rem 0;
            }}
            .ibero-instrument-row1 {{
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin-bottom: 0.4rem;
            }}
            .ibero-instrument-logo {{
                width: 36px;
                height: 36px;
                border-radius: 8px;
                object-fit: contain;
                background: {BG_BASE};
                border: 1px solid var(--ibero-border);
                flex-shrink: 0;
            }}
            .ibero-instrument-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                line-height: 1.2;
                min-width: 0;
            }}
            .ibero-instrument-name {{
                font-size: 1.35rem;
                font-weight: 700;
                color: {TEXT_MAIN};
                letter-spacing: -0.02em;
            }}
            .ibero-instrument-ticker {{
                font-size: 1.35rem;
                font-weight: 700;
                color: {TEXT_MUTED};
            }}
            .ibero-instrument-badge {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.35rem 0.5rem;
                margin: 0.2rem 0 0.45rem 0;
                padding: 0.45rem 0.65rem;
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.88rem;
                color: {TEXT_MAIN};
                background-color: {BG_INPUT};
                border: 1px solid var(--ibero-border);
                border-radius: 8px;
                line-height: 1.35;
            }}
            .ibero-instrument-badge-label {{
                font-weight: 600;
            }}
            .ibero-instrument-badge-sep {{
                color: {GOLD_DARK};
                opacity: 0.85;
            }}
            .ibero-instrument-badge-currency strong {{
                color: {TEXT_MAIN};
                font-weight: 700;
            }}
            .ibero-instrument-badge-exchange {{
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                flex-shrink: 0;
            }}
            .ibero-instrument-flag {{
                width: 20px;
                height: 14px;
                border-radius: 2px;
                object-fit: cover;
                border: 1px solid var(--ibero-border);
                flex-shrink: 0;
            }}
            .ibero-instrument-exchange {{
                font-weight: 600;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                color: {TEXT_MAIN};
            }}
            .ibero-spot-row {{
                display: flex;
                flex-wrap: wrap;
                align-items: baseline;
                gap: 0.85rem 1.25rem;
                margin: 0.75rem 0 0.35rem 0;
                min-height: 3.25rem;
            }}
            .ibero-spot-price {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 2.65rem;
                font-weight: 700;
                letter-spacing: -0.03em;
                color: {TEXT_MAIN};
                line-height: 1.1;
                flex-shrink: 0;
            }}
            .ibero-spot-change {{
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 1.35rem;
                font-weight: 600;
                line-height: 1.2;
                white-space: nowrap;
            }}
            .ibero-spot-change-up {{
                color: {CHART_UP};
            }}
            .ibero-spot-change-down {{
                color: {CHART_DOWN};
            }}
            .ibero-spot-change-text {{
                font-variant-numeric: tabular-nums;
            }}
            .ibero-spot-arrow {{
                font-size: 0.95rem;
                line-height: 1;
            }}
            [data-testid="stSegmentedControl"] {{
                width: 100%;
            }}
            [data-testid="stSegmentedControl"] button {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.82rem;
                font-weight: 600;
                color: {TEXT_MAIN};
                background-color: {BG_INPUT};
                border: 1px solid {BORDER_SUBTLE};
            }}
            [data-testid="stSegmentedControl"] button[aria-pressed="true"],
            [data-testid="stSegmentedControl"] button[data-selected="true"] {{
                background-color: {GOLD_PRIMARY};
                border-color: {GOLD_DARK};
                color: {TEXT_MAIN};
                box-shadow: inset 0 -2px 0 0 {GOLD_DARK};
            }}
            [data-testid="stSegmentedControl"] button:hover:not([aria-pressed="true"]) {{
                border-color: {GOLD_DARK};
                background-color: rgba(232, 192, 66, 0.15);
            }}
            .ibero-range-spectrum {{
                width: 100%;
                max-width: 100%;
                margin: 0.35rem 0 0.65rem 0;
                padding: 0.35rem 0.1rem 0.25rem 0.1rem;
                box-sizing: border-box;
            }}
            .ibero-range-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.78rem;
                font-weight: 600;
                color: {TEXT_MAIN};
                margin: 0 0 0.45rem 0;
                line-height: 1.2;
            }}
            .ibero-range-track-wrap {{
                position: relative;
                width: 100%;
                height: 1.35rem;
                margin-bottom: 0.35rem;
            }}
            .ibero-range-track {{
                position: absolute;
                left: 0;
                right: 0;
                top: 50%;
                transform: translateY(-50%);
                height: 5px;
                border-radius: 999px;
                background-color: {BORDER_SUBTLE};
            }}
            .ibero-range-marker {{
                position: absolute;
                top: -0.05rem;
                transform: translateX(-50%);
                font-size: 0.85rem;
                line-height: 1;
                color: {GOLD_DARK};
                font-weight: 700;
                cursor: default;
                z-index: 2;
            }}
            .ibero-range-labels {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 0.35rem;
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.82rem;
                color: {TEXT_MAIN};
                font-variant-numeric: tabular-nums;
            }}
            .ibero-range-min,
            .ibero-range-max {{
                flex: 0 1 auto;
            }}
            .ibero-range-current {{
                flex: 0 1 auto;
                font-weight: 700;
                color: {GOLD_DARK};
                text-align: center;
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
            [class*="st-key-sandbox_notebook_panel"] [class*="st-key-ace_editor"] {{
                border: 1px solid {BORDER_SUBTLE} !important;
                border-radius: 6px;
                overflow: hidden;
                background-color: {BG_BASE};
                box-shadow: none;
            }}
            [class*="st-key-ace_editor"] {{
                border: 1.5px solid {GOLD_DARK};
                border-radius: 8px;
                overflow: hidden;
                background-color: {BG_INPUT};
                box-shadow: 0 1px 4px rgba(73, 70, 70, 0.06);
            }}
            [class*="st-key-ace_editor"] > div {{
                border-radius: 7px;
            }}
            [class*="st-key-ace_editor"] .ace_editor {{
                border-radius: 6px;
                font-family: ui-monospace, "Cascadia Code", "Source Code Pro", monospace;
            }}
            [class*="st-key-sandbox_portfolio_panel"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
                background-color: {BG_INPUT} !important;
                border: 1.5px solid {GOLD_DARK} !important;
                border-radius: 8px;
            }}
            [class*="st-key-sandbox_portfolio_panel"] [data-testid="stTextInput"] input {{
                background-color: {BG_INPUT} !important;
                border: 1.5px solid {GOLD_DARK} !important;
                border-radius: 8px;
                color: {TEXT_MAIN};
                font-size: 0.85rem;
            }}
            [class*="st-key-sandbox_portfolio_panel"] [data-testid="stTextInput"] label {{
                font-size: 0.8rem;
                color: {TEXT_MUTED};
            }}
            div[data-testid="stVerticalBlock"][class*="st-key-sandbox_notebook_panel"] {{
                margin-top: 0.25rem;
                padding: 0.35rem 0.45rem 0.5rem !important;
                border: 1px solid {BORDER_SUBTLE} !important;
                border-color: {BORDER_SUBTLE} !important;
                border-radius: 6px !important;
                box-shadow: none !important;
                outline: none !important;
                background-color: {BG_BASE};
            }}
            [class*="st-key-sandbox_notebook_panel"] [data-testid="stVerticalBlock"] {{
                gap: 0 !important;
            }}
            [class*="st-key-sandbox_notebook_panel"] [data-testid="stElementContainer"] {{
                margin-top: 0 !important;
                margin-bottom: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"]) {{
                background-color: {BG_BASE};
                border: none;
                border-bottom: 1px solid {BORDER_SUBTLE};
                border-radius: 0;
                padding: 0.25rem 0.35rem;
                margin: 0;
                align-items: center;
                gap: 0.15rem;
            }}
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(.ibero-sandbox-styles-anchor),
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(.ibero-sandbox-run-marker),
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(.ibero-sandbox-styles-anchor)
            [data-testid="stMarkdownContainer"],
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(.ibero-sandbox-run-marker)
            [data-testid="stMarkdownContainer"] {{
                display: none !important;
                margin: 0 !important;
                padding: 0 !important;
                height: 0 !important;
                min-height: 0 !important;
                overflow: hidden !important;
                line-height: 0 !important;
            }}
            [class*="st-key-sandbox_notebook_panel"] .ibero-sandbox-styles-anchor {{
                display: none !important;
                height: 0;
                margin: 0;
                padding: 0;
            }}
            [class*="st-key-sandbox_notebook_panel"] .ibero-sandbox-run-marker {{
                display: none !important;
                height: 0;
                margin: 0;
                padding: 0;
            }}
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(.ibero-sandbox-run-marker),
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(.ibero-sandbox-run-marker)
            [data-testid="stMarkdownContainer"] {{
                display: none !important;
                margin: 0 !important;
                padding: 0 !important;
                height: 0 !important;
                min-height: 0 !important;
                overflow: hidden !important;
                line-height: 0 !important;
            }}
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has([class*="st-key-sandbox_cell_"]) {{
                margin-top: 0 !important;
                padding-top: 0 !important;
            }}
            [class*="st-key-sandbox_notebook_panel"] iframe[title="streamlit_components_v1.html"],
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(
                iframe[title="streamlit_components_v1.html"]
            ),
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stElementContainer"]:has(iframe[title="streamlit_components_v1.html"])
            iframe,
            [class*="st-key-sandbox_kbd_bridge"] [data-testid="stElementContainer"],
            [class*="st-key-sandbox_kbd_bridge"] iframe {{
                height: 0 !important;
                min-height: 0 !important;
                max-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                overflow: hidden !important;
            }}
            div[data-testid="stVerticalBlock"][class*="st-key-sandbox_kbd_bridge"] {{
                height: 0 !important;
                min-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }}
            [class*="st-key-sandbox_run_mobile"] {{
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                overflow: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
            [class*="st-key-sandbox_run_mobile"] button {{
                pointer-events: auto !important;
            }}
            [class*="st-key-sandbox_tb_"] [data-testid="stColumn"] {{
                min-width: 2.25rem;
            }}
            [class*="st-key-sandbox_tb_"] button {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0.35rem 0.45rem !important;
                min-height: 2rem;
                min-width: 2rem;
                border-radius: 4px !important;
                color: {TEXT_MUTED} !important;
            }}
            [class*="st-key-sandbox_tb_"] button:hover {{
                background-color: rgba(73, 70, 70, 0.08) !important;
                color: {TEXT_MAIN} !important;
            }}
            [class*="st-key-sandbox_tb_"] button:active {{
                background-color: rgba(73, 70, 70, 0.12) !important;
            }}
            [class*="st-key-sandbox_tb_"] button:focus-visible {{
                outline: 1px solid {BORDER_SUBTLE};
                outline-offset: 1px;
            }}
            [class*="st-key-sandbox_tb_"] button [data-testid="stIconMaterial"],
            [class*="st-key-sandbox_tb_"] button svg {{
                fill: {TEXT_MUTED} !important;
                color: {TEXT_MUTED} !important;
                font-size: 1.25rem;
                width: 1.25rem;
                height: 1.25rem;
            }}
            [class*="st-key-sandbox_tb_"] button:hover [data-testid="stIconMaterial"],
            [class*="st-key-sandbox_tb_"] button:hover svg {{
                fill: {TEXT_MAIN} !important;
                color: {TEXT_MAIN} !important;
            }}
            [class*="st-key-sandbox_tb_"] [data-testid="stMarkdownContainer"] {{
                display: none;
            }}
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"])
            > div[data-testid="stColumn"]:last-child,
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"])
            > div[data-testid="stColumn"]:last-child > div {{
                display: flex !important;
                justify-content: flex-end;
                align-items: center !important;
                align-self: center;
                height: 100%;
                min-height: 2rem;
                margin: 0;
                padding: 0;
            }}
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"])
            > div[data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] {{
                justify-content: center;
                gap: 0;
                padding: 0;
                margin: 0;
            }}
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"])
            > div[data-testid="stColumn"]:last-child
            [data-testid="stElementContainer"],
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"])
            > div[data-testid="stColumn"]:last-child
            .element-container {{
                display: flex !important;
                align-items: center !important;
                justify-content: flex-end;
                margin: 0 !important;
                padding: 0 !important;
                min-height: 2rem;
            }}
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"])
            > div[data-testid="stColumn"]:last-child
            [data-testid="stMarkdownContainer"] {{
                display: flex !important;
                align-items: center;
                justify-content: flex-end;
                width: 100%;
                margin: 0;
                padding: 0;
            }}
            .ibero-sandbox-toolbar-status {{
                margin: 0;
                padding: 0 0.35rem 0 0;
                font-size: 0.82rem;
                color: {TEXT_MUTED};
                line-height: 1.35;
                text-align: right;
                display: block;
                min-height: 2rem;
            }}
            .ibero-sandbox-toolbar-status-inner {{
                display: inline-flex;
                align-items: center;
                justify-content: flex-end;
                flex-wrap: wrap;
                gap: 0.35em;
                white-space: normal;
            }}
            .ibero-sandbox-toolbar-status strong {{
                color: {TEXT_MAIN};
                font-weight: 600;
            }}
            [class*="st-key-sandbox_notebook_panel"]
            [data-testid="stHorizontalBlock"]:not(:has([class*="st-key-sandbox_tb_"])) {{
                padding: 0 0.45rem 0.35rem;
                margin: 0;
            }}
            [class*="st-key-sandbox_notebook_panel"] [class*="st-key-sandbox_cell_"]
            div[data-testid="stHorizontalBlock"] {{
                align-items: flex-start;
            }}
            [class*="st-key-sandbox_notebook_panel"] .ibero-sandbox-cell-badge {{
                line-height: 1.2;
                user-select: none;
            }}
            [class*="st-key-sandbox_notebook_panel"] [class*="st-key-sandbox_select_"] button,
            [class*="st-key-sandbox_notebook_panel"] [class*="st-key-sandbox_run_mobile"] button,
            [class*="st-key-sandbox_notebook_panel"] button[kind="primary"],
            [class*="st-key-sandbox_notebook_panel"] button[data-testid="stBaseButton-primary"] {{
                font-family: ui-monospace, "Cascadia Code", "Source Code Pro", monospace;
                font-weight: 600;
                font-size: 0.82rem;
                background-color: {BG_BASE} !important;
                border: 1px solid {BORDER_SUBTLE} !important;
                color: {TEXT_MAIN} !important;
                box-shadow: none !important;
            }}
            [class*="st-key-sandbox_notebook_panel"] [class*="st-key-sandbox_select_"] button:hover,
            [class*="st-key-sandbox_notebook_panel"] [class*="st-key-sandbox_run_mobile"] button:hover {{
                background-color: {BG_INPUT} !important;
                border-color: {BORDER_SIDEBAR} !important;
                color: {TEXT_MAIN} !important;
            }}
            [class*="st-key-sandbox_notebook_panel"] button[kind="primary"],
            [class*="st-key-sandbox_notebook_panel"] button[data-testid="stBaseButton-primary"] {{
                background-color: {BG_INPUT} !important;
                border-color: {BORDER_SIDEBAR} !important;
            }}
            [class*="st-key-sandbox_select_"] button {{
                font-family: ui-monospace, "Cascadia Code", "Source Code Pro", monospace;
                font-weight: 600;
                font-size: 0.82rem;
            }}
            @media (min-width: 769px) {{
                [class*="st-key-sandbox_run_mobile"] {{
                    display: block !important;
                }}
            }}
            @media (max-width: 768px) {{
                div[data-testid="stHorizontalBlock"]:has([class*="st-key-sandbox_tb_"]) {{
                    flex-wrap: wrap;
                }}
                [class*="st-key-sandbox_run_mobile"] button {{
                    min-height: 2.75rem;
                }}
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


