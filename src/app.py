"""
Baromedr Cymru Wave 2 — Interactive Analysis Dashboard

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.section_pages.at_a_glance import render_at_a_glance
from src.section_pages.concerns_and_risks import render_concerns_and_risks
from src.section_pages.data_notes import render_data_notes
from src.section_pages.demographics_and_types import render_demographics_and_types
from src.section_pages.earned_settlement import render_earned_settlement
from src.section_pages.overview import render_overview
from src.section_pages.trends_and_waves import render_trends_and_waves
from src.section_pages.volunteer_recruitment import render_volunteer_recruitment
from src.section_pages.volunteer_retention import render_volunteer_retention
from src.section_pages.workforce_and_operations import render_workforce_and_operations

from src.config import (
    CONCERNS_LABELS,
    K_ANON_THRESHOLD,
    ORG_SIZE_ORDER,
    GlobalStreamlitAppUISharedConfigState,
)
from src.data_loader import load_dataset
from src.eda import profile_summary
from src.navigation import get_default_page, render_sidebar_nav
from src.section_pages.executive_summary import render_executive_summary

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Baromedr Cymru W2 — Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

GlobalStreamlitAppUISharedConfigState.text_size_mode = st.sidebar.radio(
    "Chart label size",
    ["Normal", "Larger"],
    index=0,
)
GlobalStreamlitAppUISharedConfigState.text_scale = (
    1.0 if GlobalStreamlitAppUISharedConfigState.text_size_mode == "Normal" else 1.3
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------


@st.cache_data
def get_data():
    return load_dataset()


df_full = (
    get_data()
)  # Analysis DataFrame used throughout the app (includes derived columns). # noqa

# ---------------------------------------------------------------------------
# Sidebar: filters + accessibility toggle
# ---------------------------------------------------------------------------
st.sidebar.title("Baromedr Cymru")
st.sidebar.caption("Wave 2 Analysis Dashboard")
st.sidebar.divider()

GlobalStreamlitAppUISharedConfigState.accessible_mode = st.sidebar.checkbox(
    "Colour-blind friendly mode", value=False
)
GlobalStreamlitAppUISharedConfigState.palette_mode = (
    "accessible" if GlobalStreamlitAppUISharedConfigState.accessible_mode else "brand"
)

st.sidebar.divider()
st.sidebar.subheader("Filters")

GlobalStreamlitAppUISharedConfigState.size_options = ["All"] + ORG_SIZE_ORDER
GlobalStreamlitAppUISharedConfigState.selected_size = st.sidebar.selectbox(
    "Organisation size", GlobalStreamlitAppUISharedConfigState.size_options
)

GlobalStreamlitAppUISharedConfigState.scope_options = ["All"] + sorted(
    df_full["wales_scope"].dropna().unique().tolist()
)
GlobalStreamlitAppUISharedConfigState.selected_scope = st.sidebar.selectbox(
    "Geographic scope", GlobalStreamlitAppUISharedConfigState.scope_options
)

GlobalStreamlitAppUISharedConfigState.la_scope_options = ["All"] + sorted(
    df_full["location_la_primary"].dropna().unique().tolist()
)
GlobalStreamlitAppUISharedConfigState.selected_la_scope = st.sidebar.selectbox(
    "Local primary authority scope",
    GlobalStreamlitAppUISharedConfigState.la_scope_options,
)

GlobalStreamlitAppUISharedConfigState.activity_options = ["All"] + sorted(
    df_full["mainactivity"].dropna().unique().tolist()
)
GlobalStreamlitAppUISharedConfigState.selected_activity = st.sidebar.selectbox(
    "Main activity", GlobalStreamlitAppUISharedConfigState.activity_options
)

GlobalStreamlitAppUISharedConfigState.paid_staff_options = [
    "All",
    "Has paid staff",
    "No paid staff",
]
GlobalStreamlitAppUISharedConfigState.selected_paid_staff = st.sidebar.selectbox(
    "Paid staff", GlobalStreamlitAppUISharedConfigState.paid_staff_options
)

GlobalStreamlitAppUISharedConfigState.concern_label_options = list(
    CONCERNS_LABELS.values()
)
GlobalStreamlitAppUISharedConfigState.selected_concerns = st.sidebar.multiselect(
    "Organisations that cited concern",
    options=GlobalStreamlitAppUISharedConfigState.concern_label_options,
)

df = df_full.copy()

# Apply filters (if selected, default is "All")
if GlobalStreamlitAppUISharedConfigState.selected_size != "All":
    df = df[df["org_size"] == GlobalStreamlitAppUISharedConfigState.selected_size]
if GlobalStreamlitAppUISharedConfigState.selected_scope != "All":
    df = df[df["wales_scope"] == GlobalStreamlitAppUISharedConfigState.selected_scope]
if GlobalStreamlitAppUISharedConfigState.selected_la_scope != "All":
    df = df[
        df["location_la_primary"]
        == GlobalStreamlitAppUISharedConfigState.selected_la_scope
    ]
if GlobalStreamlitAppUISharedConfigState.selected_activity != "All":
    df = df[
        df["mainactivity"] == GlobalStreamlitAppUISharedConfigState.selected_activity
    ]
if GlobalStreamlitAppUISharedConfigState.selected_paid_staff == "Has paid staff":
    df = df[df["paidworkforce"] == "Yes"]
elif GlobalStreamlitAppUISharedConfigState.selected_paid_staff == "No paid staff":
    df = df[df["paidworkforce"] == "No"]

if GlobalStreamlitAppUISharedConfigState.selected_concerns:
    label_to_column = {v: k for k, v in CONCERNS_LABELS.items()}
    concern_columns = [
        label_to_column[label]
        for label in GlobalStreamlitAppUISharedConfigState.selected_concerns
        if label in label_to_column
    ]
    if concern_columns:
        mask = pd.Series(False, index=df.index)
        for col in concern_columns:
            if col in df.columns:
                mask = mask | df[col].notna()
        df = df[mask]

n = len(df)

GlobalStreamlitAppUISharedConfigState.base_size_n = n

GlobalStreamlitAppUISharedConfigState.suppressed = n < K_ANON_THRESHOLD

if GlobalStreamlitAppUISharedConfigState.suppressed:
    st.sidebar.warning(
        f"⚠️ Only **{n}** organisations match these filters (below the privacy "
        f"threshold of {K_ANON_THRESHOLD}). Results are suppressed to protect respondent anonymity."
    )

st.sidebar.divider()
st.sidebar.caption(f"Showing **{n}** of {len(df_full)} organisations")

# ---------------------------------------------------------------------------
# Navigation: WCVA pill-style sidebar
# ---------------------------------------------------------------------------

page = render_sidebar_nav(st.session_state.get("current_page", get_default_page()))

prof = profile_summary(df)

# =========================================================================
# PAGE 1: At-a-Glance Infographic
# =========================================================================
if page == "At-a-Glance":
    render_at_a_glance(df, n, GlobalStreamlitAppUISharedConfigState.accessible_mode)

# =========================================================================
# PAGE 2: Overview
# =========================================================================
elif page == "Overview":
    render_overview(
        df,
        suppressed=GlobalStreamlitAppUISharedConfigState.suppressed,
        n=n,
        palette_mode=GlobalStreamlitAppUISharedConfigState.palette_mode,
        prof=prof,
    )


# =========================================================================
# PAGE 3: Volunteer Recruitment
# =========================================================================
elif page == "Volunteer Recruitment":
    render_volunteer_recruitment(df, n)

# =========================================================================
# PAGE 4: Volunteer Retention
# =========================================================================
elif page == "Volunteer Retention":
    render_volunteer_retention(df, n)

# =========================================================================
# PAGE 5: Trends & Waves
# =========================================================================
elif page == "Trends & Waves":
    render_trends_and_waves(df_full)

# =========================================================================
# PAGE 6: Workforce & Operations
# =========================================================================
elif page == "Workforce & Operations":
    render_workforce_and_operations(df, n)

# =========================================================================
# PAGE 7: Concerns & Risks
# =========================================================================
elif page == "Concerns & Risks":
    render_concerns_and_risks(df, n)

# =========================================================================
# PAGE 8: Demographics & Types
# =========================================================================
elif page == "Demographics & Types":
    render_demographics_and_types(df, n)

# =========================================================================
# PAGE 9: Earned Settlement
# =========================================================================
elif page == "Earned Settlement":
    render_earned_settlement(df, n)

# =========================================================================
# PAGE 10: Executive Summary
# =========================================================================
elif page == "Executive Summary":
    render_executive_summary(df, GlobalStreamlitAppUISharedConfigState.suppressed)


# =========================================================================
# PAGE 11: Data Notes
# =========================================================================
elif page == "Data Notes":
    render_data_notes(df_full)
