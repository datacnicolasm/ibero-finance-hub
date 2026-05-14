"""Global theme CSS for Streamlit (visual layer only)."""

from __future__ import annotations

import streamlit as st

EMERALD = "#10b981"
RUBY = "#f43f5e"
SLATE_950 = "#020617"
SLATE_900 = "#0f172a"
SLATE_800 = "#1e293b"
BLUE_DEEP = "#1e3a5f"
COBALT = "#133c6a"
COBALT_ACTIVE_BG = "rgba(19, 60, 106, 0.38)"
COBALT_ACCENT = "#1e5a9e"


def get_option_menu_styles() -> dict[str, dict[str, str]]:
    """Inline styles for ``streamlit_option_menu.option_menu`` (sidebar)."""
    return {
        "container": {
            "padding": "0",
            "background-color": "transparent",
        },
        "menu-title": {"display": "none"},
        "icon": {
            "color": "#94a3b8",
            "font-size": "1.05rem",
        },
        "nav-link": {
            "font-family": "ui-sans-serif, system-ui, sans-serif",
            "font-size": "0.88rem",
            "font-weight": "500",
            "color": "#cbd5e1",
            "padding": "0.55rem 0.65rem",
            "margin": "0.12rem 0",
            "border": "none",
            "border-radius": "9px",
        },
        "nav-link-selected": {
            "background-color": COBALT_ACTIVE_BG,
            "color": "#f8fafc",
            "font-weight": "600",
            "border": "none",
            "border-radius": "9px",
            "box-shadow": f"inset 3px 0 0 0 {COBALT_ACCENT}",
        },
    }


def inject_global_styles() -> None:
    """Inject app-wide CSS (dark Bloomberg-like theme)."""
    st.markdown(
        f"""
        <style>
            :root {{
                --ibero-bg: {SLATE_950};
                --ibero-panel: {SLATE_900};
                --ibero-border: {SLATE_800};
                --ibero-accent: {BLUE_DEEP};
                --ibero-positive: {EMERALD};
                --ibero-negative: {RUBY};
            }}
            .stApp {{
                background: linear-gradient(165deg, {SLATE_950} 0%, #0a1628 45%, {SLATE_900} 100%);
                color: #e2e8f0;
            }}
            [data-testid="stHeader"] {{
                background-color: rgba(15, 23, 42, 0.85);
                border-bottom: 1px solid {SLATE_800};
            }}
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #0a0f18 0%, {SLATE_900} 55%, #0c1424 100%);
                border-right: none;
            }}
            [data-testid="stSidebar"] > div:first-child {{
                padding-top: 0.35rem;
            }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {{
                color: #cbd5e1 !important;
            }}
            .ibero-side-brand {{
                display: flex;
                align-items: center;
                gap: 0.65rem;
                padding: 0.25rem 0.15rem 1rem 0.15rem;
            }}
            .ibero-side-logo {{
                width: 38px;
                height: 38px;
                border-radius: 10px;
                background: linear-gradient(145deg, {COBALT} 0%, {BLUE_DEEP} 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                box-shadow: 0 6px 18px rgba(0,0,0,0.35);
            }}
            .ibero-side-logo span {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-weight: 800;
                font-size: 0.72rem;
                letter-spacing: 0.06em;
                color: #f8fafc;
            }}
            .ibero-side-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-weight: 700;
                font-size: 0.74rem;
                letter-spacing: 0.2em;
                line-height: 1.2;
                color: #e2e8f0;
            }}
            .ibero-side-title .sub {{
                display: block;
                font-size: 0.58rem;
                font-weight: 500;
                letter-spacing: 0.1em;
                color: #64748b;
                margin-top: 0.2rem;
                text-transform: none;
            }}
            .ibero-nav-footer {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.68rem;
                letter-spacing: 0.03em;
                color: #64748b;
                text-align: center;
                padding: 1.5rem 0.35rem 0.5rem 0.35rem;
                line-height: 1.45;
            }}
            div[data-testid="stMetric"] {{
                background: rgba(30, 58, 95, 0.25);
                border: 1px solid {SLATE_800};
                border-radius: 10px;
                padding: 0.75rem 1rem;
            }}
            div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
                color: #f8fafc;
            }}
            .ibero-hero {{
                background: linear-gradient(135deg, rgba(30,58,95,0.5) 0%, rgba(15,23,42,0.9) 100%);
                border: 1px solid {SLATE_800};
                border-radius: 14px;
                padding: 1.75rem 2rem;
                margin-bottom: 1.25rem;
                box-shadow: 0 12px 40px rgba(0,0,0,0.35);
            }}
            .ibero-hero h1 {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: #f1f5f9;
                margin: 0 0 0.5rem 0;
                font-size: 1.85rem;
            }}
            .ibero-hero p {{
                color: #94a3b8;
                margin: 0;
                line-height: 1.55;
                max-width: 720px;
            }}
            .ibero-kicker {{
                color: {EMERALD};
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                margin-bottom: 0.35rem;
            }}
            .ibero-tm-panel {{
                background: rgba(15, 23, 42, 0.5);
                border: 1px solid rgba(51, 65, 85, 0.55);
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
                color: #94a3b8;
                margin: 0 0 0.65rem 0;
            }}
            .ibero-tm-foot {{
                font-size: 0.72rem;
                color: #64748b;
                line-height: 1.45;
                padding: 0.5rem 0.25rem 0 0.25rem;
                border-top: 1px solid rgba(51, 65, 85, 0.35);
                margin-top: 0.75rem;
            }}
            .ibero-stats-title {{
                font-family: ui-sans-serif, system-ui, sans-serif;
                font-size: 0.82rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #94a3b8;
                margin: 0 0 0.65rem 0;
            }}
            div[data-testid="stDataFrame"] {{
                width: 100% !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
