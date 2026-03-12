from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import streamlit as st

from src.config import WCVA_BRAND


@dataclass(frozen=True)
class NavItem:
    """Configuration for a single sidebar navigation entry."""

    id: str
    label: str
    subtitle: str | None = None
    icon: str | None = None


# Keep IDs aligned with the existing page dispatch values in app.py
NAV_ITEMS: List[NavItem] = [
    NavItem(
        "Executive Summary",
        "Executive Summary",
        "Headline story and KPIs",
        "📊",
    ),
    NavItem(
        "At-a-Glance",
        "At-a-Glance",
        "Poster-style infographic",
        "🖼️",
    ),
    NavItem(
        "Overview",
        "Overview",
        "Profile and recent experience",
        "📋",
    ),
    NavItem(
        "Trends & Waves",
        "Trends & Waves",
        "Cross-wave trends",
        "📈",
    ),
    NavItem(
        "Volunteer Recruitment",
        "Volunteer Recruitment",
        "Finding new volunteers",
        "🧲",
    ),
    NavItem(
        "Volunteer Retention",
        "Volunteer Retention",
        "Keeping volunteers",
        "🧡",
    ),
    NavItem(
        "Workforce & Operations",
        "Workforce & Operations",
        "Staffing and capacity",
        "🧑‍🤝‍🧑",
    ),
    NavItem(
        "Concerns & Risks",
        "Concerns & Risks",
        "Pressures and risk factors",
        "⚠️",
    ),
    NavItem(
        "Demographics & Types",
        "Demographics & Types",
        "Who volunteers and how",
        "👥",
    ),
    NavItem(
        "Earned Settlement",
        "Earned Settlement",
        "Volunteering for earned settlement",
        "🏛️",
    ),
    NavItem("Data Notes", "Data Notes", "Technical notes and methods", "📑"),
]


def get_default_page() -> str:
    """Return the default starting page ID."""
    return NAV_ITEMS[0].id


def get_nav_item_ids(items: Iterable[NavItem] | None = None) -> list[str]:
    """Return the list of page IDs in navigation order."""
    source = items or NAV_ITEMS
    return [item.id for item in source]


def render_sidebar_nav(current_page: str | None = None) -> str:
    """Render the WCVA sidebar navigation and return the selected page ID.

    This version uses simple Streamlit buttons plus short subtitles so
    behaviour is robust and the layout remains clean.
    """

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = current_page or get_default_page()

    valid_ids = set(get_nav_item_ids())
    if st.session_state["current_page"] not in valid_ids:
        st.session_state["current_page"] = get_default_page()

    current = st.session_state["current_page"]

    # WCVA-inspired teal styling for sidebar buttons
    css = """
    <style>
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: TEAL;
        border-color: TEAL;
        color: #FFFFFF;
    }

    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: TEAL_DARK;
        border-color: TEAL_DARK;
        color: #FFFFFF;
    }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #FFFFFF;
        color: NAVY;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #F5F7FB;
        border-color: #D6DEEE;
        color: NAVY;
    }
    </style>
    """
    css = (
        css.replace("TEAL_DARK", "#006b63")
        .replace("TEAL", WCVA_BRAND["teal"])
        .replace("NAVY", WCVA_BRAND["navy"])
    )
    st.sidebar.markdown(css, unsafe_allow_html=True)

    st.sidebar.subheader("Sections")

    for item in NAV_ITEMS:
        is_active = item.id == current

        # Use primary style for the active section so it stands out.
        button_type = "primary" if is_active else "secondary"

        label = f"{item.icon}  {item.label}" if item.icon else item.label

        clicked = st.sidebar.button(
            label,
            key=f"nav_btn_{item.id}",
            use_container_width=True,
            type=button_type,
        )
        if item.subtitle:
            # Lightweight description under each button.
            st.sidebar.caption(item.subtitle)

        if clicked and not is_active:
            st.session_state["current_page"] = item.id
            st.rerun()

    return st.session_state["current_page"]
