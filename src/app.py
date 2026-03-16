# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
Baromedr Cymru Wave 2 — Interactive Analysis Dashboard

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.config import (
    CONCERNS_LABELS,
    K_ANON_THRESHOLD,
    ORG_SIZE_ORDER,
    RuntimeDataSource,
    display_runtime_source,
    get_app_ui_config,
)
from src.data_loader import check_runtime_assets, load_dataset
from src.eda import profile_summary
from src.navigation import get_default_page, render_sidebar_nav
from src.section_pages.at_a_glance import render_at_a_glance
from src.section_pages.concerns_and_risks import render_concerns_and_risks
from src.section_pages.data_notes import render_data_notes
from src.section_pages.demographics_and_types import render_demographics_and_types
from src.section_pages.deployment_health import render_deployment_health
from src.section_pages.earned_settlement import render_earned_settlement
from src.section_pages.executive_summary import render_executive_summary
from src.section_pages.overview import render_overview
from src.section_pages.sroi_references import render_sroi_references
from src.section_pages.trends_and_waves import render_trends_and_waves
from src.section_pages.volunteer_recruitment import render_volunteer_recruitment
from src.section_pages.volunteer_retention import render_volunteer_retention
from src.section_pages.workforce_and_operations import render_workforce_and_operations

DEBUG_MEMORY = os.environ.get("WCVA_DEBUG_MEMORY", "").lower() in ("1", "true", "yes")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Baromedr Cymru W2 — Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------


@st.cache_data
def get_data() -> tuple[pd.DataFrame, RuntimeDataSource]:
    """Load and return the main analysis dataset plus runtime source metadata."""
    df, source = load_dataset(return_source=True)
    assert isinstance(
        source, RuntimeDataSource
    ), "load_dataset(return_source=True) must return RuntimeDataSource metadata"
    return df, source


df_full, dataset_source = get_data()
asset_report = check_runtime_assets()
is_demo_mode = bool(getattr(dataset_source, "is_demo", False))

if is_demo_mode:
    st.warning(
        "Demo / sample data mode is active. The private Wave dataset could not be "
        "resolved, so the app is using the bundled fixture dataset. Treat all "
        "figures as demonstration outputs only."
    )
    st.caption(
        f"Resolved dataset source: `{display_runtime_source(dataset_source)}` "
        f"({dataset_source.source_type})."
    )
elif asset_report["missing_required"]:
    st.warning(
        "Some runtime prerequisites are missing or incomplete. Review the "
        "Deployment Health page before trusting this environment."
    )

# ---------------------------------------------------------------------------
# Sidebar: filters + accessibility toggle
# ---------------------------------------------------------------------------
st.sidebar.title("Baromedr Cymru")
st.sidebar.caption(
    "Wave 2 Analysis Dashboard" + (" — DEMO / SAMPLE DATA" if is_demo_mode else "")
)
if is_demo_mode:
    st.sidebar.warning("Demo mode: running from the bundled sample dataset.")
st.sidebar.divider()

st.sidebar.subheader("Accessibility & Display")

ui_config = get_app_ui_config()

with st.sidebar.container():
    st.caption(
        "Tune how charts are displayed for readability and colour accessibility. "
        "These settings only affect your session."
    )

    _radio_options = ["Normal", "Larger"]
    if ui_config.text_size_mode not in _radio_options:
        ui_config.text_size_mode = "Normal"

    ui_config.text_size_mode = st.radio(
        "Text size for charts",
        _radio_options,
        index=_radio_options.index(ui_config.text_size_mode),
        key="ui_text_size_mode",
        horizontal=True,
        help="Larger text can improve readability on projectors or smaller screens.",
    )
    ui_config.text_scale = 1.0 if ui_config.text_size_mode == "Normal" else 1.3

    ui_config.accessible_mode = st.checkbox(
        "Colour-blind friendly palette",
        key="ui_accessible_mode",
        value=ui_config.accessible_mode,
        help=(
            "Use a palette designed for common colour-vision conditions while "
            "keeping WCVA branding where possible."
        ),
    )
    ui_config.palette_mode = "accessible" if ui_config.accessible_mode else "brand"

st.sidebar.divider()
st.sidebar.subheader("Filters")

ui_config.size_options = ["All"] + ORG_SIZE_ORDER
_size_idx = (
    ui_config.size_options.index(ui_config.selected_size)
    if ui_config.selected_size in ui_config.size_options
    else 0
)
ui_config.selected_size = st.sidebar.selectbox(
    "Organisation size", ui_config.size_options, index=_size_idx
)

ui_config.scope_options = ["All"] + sorted(
    df_full["wales_scope"].dropna().unique().tolist()
)
_scope_idx = (
    ui_config.scope_options.index(ui_config.selected_scope)
    if ui_config.selected_scope in ui_config.scope_options
    else 0
)
ui_config.selected_scope = st.sidebar.selectbox(
    "Geographic scope", ui_config.scope_options, index=_scope_idx
)

ui_config.la_scope_options = ["All"] + sorted(
    df_full["location_la_primary"].dropna().unique().tolist()
)
_la_idx = (
    ui_config.la_scope_options.index(ui_config.selected_la_scope)
    if ui_config.selected_la_scope in ui_config.la_scope_options
    else 0
)
ui_config.selected_la_scope = st.sidebar.selectbox(
    "Local primary authority scope",
    ui_config.la_scope_options,
    index=_la_idx,
)

ui_config.activity_options = ["All"] + sorted(
    df_full["mainactivity"].dropna().unique().tolist()
)
_activity_idx = (
    ui_config.activity_options.index(ui_config.selected_activity)
    if ui_config.selected_activity in ui_config.activity_options
    else 0
)
ui_config.selected_activity = st.sidebar.selectbox(
    "Main activity", ui_config.activity_options, index=_activity_idx
)

ui_config.paid_staff_options = [
    "All",
    "Has paid staff",
    "No paid staff",
]
_paid_idx = (
    ui_config.paid_staff_options.index(ui_config.selected_paid_staff)
    if ui_config.selected_paid_staff in ui_config.paid_staff_options
    else 0
)
ui_config.selected_paid_staff = st.sidebar.selectbox(
    "Paid staff", ui_config.paid_staff_options, index=_paid_idx
)

ui_config.concern_label_options = list(CONCERNS_LABELS.values())
ui_config.selected_concerns = st.sidebar.multiselect(
    "Organisations that cited concern",
    options=ui_config.concern_label_options,
    default=ui_config.selected_concerns or [],
)

df = df_full

# Apply filters (if selected, default is "All")
if ui_config.selected_size != "All":
    df = df[df["org_size"] == ui_config.selected_size]
if ui_config.selected_scope != "All":
    df = df[df["wales_scope"] == ui_config.selected_scope]
if ui_config.selected_la_scope != "All":
    df = df[df["location_la_primary"] == ui_config.selected_la_scope]
if ui_config.selected_activity != "All":
    df = df[df["mainactivity"] == ui_config.selected_activity]
if ui_config.selected_paid_staff == "Has paid staff":
    df = df[df["paidworkforce"] == "Yes"]
elif ui_config.selected_paid_staff == "No paid staff":
    df = df[df["paidworkforce"] == "No"]

if ui_config.selected_concerns:
    label_to_column = {v: k for k, v in CONCERNS_LABELS.items()}
    concern_columns = [
        label_to_column[label]
        for label in ui_config.selected_concerns
        if label in label_to_column
    ]
    if concern_columns:
        mask = pd.Series(False, index=df.index)
        for col in concern_columns:
            if col in df.columns:
                mask = mask | df[col].notna()
        df = df[mask]

n = len(df)

ui_config.base_size_n = n

ui_config.suppressed = n < K_ANON_THRESHOLD

if ui_config.suppressed:
    st.sidebar.warning(
        f"⚠️ Only **{n}** organisations match these filters (below the privacy "
        f"threshold of {K_ANON_THRESHOLD}). Results are suppressed to protect respondent anonymity."
    )

st.sidebar.divider()
st.sidebar.caption(f"Showing **{n}** of {len(df_full)} organisations")
if DEBUG_MEMORY:
    import psutil

    process = psutil.Process(os.getpid())
    st.sidebar.caption(f"Memory: {process.memory_info().rss / 1024**2:.1f} MB")

st.sidebar.divider()
st.sidebar.caption(
    "Source code available under AGPLv3: "
    "https://github.com/nba1990/wcva_data_analysis"
)

# ---------------------------------------------------------------------------
# Navigation: WCVA pill-style sidebar
# ---------------------------------------------------------------------------

page = render_sidebar_nav(st.session_state.get("current_page", get_default_page()))

prof = profile_summary(df)

# =========================================================================
# PAGE 1: At-a-Glance Infographic
# =========================================================================
if page == "At-a-Glance":
    render_at_a_glance(df, n, ui_config.accessible_mode)

# =========================================================================
# PAGE 2: Overview
# =========================================================================
elif page == "Overview":
    render_overview(
        df,
        suppressed=ui_config.suppressed,
        n=n,
        palette_mode=ui_config.palette_mode,
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
    render_trends_and_waves(df)

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
    render_executive_summary(df, ui_config.suppressed)


# =========================================================================
# PAGE 11: SROI & References
# =========================================================================
elif page == "SROI & References":
    render_sroi_references()


# =========================================================================
# PAGE 12: Deployment Health
# =========================================================================
elif page == "Deployment Health":
    render_deployment_health(asset_report, df_full)


# =========================================================================
# PAGE 13: Data Notes
# =========================================================================
elif page == "Data Notes":
    render_data_notes(df)


# ---------------------------------------------------------------------------
# Global footer (shown on every page)
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Source code available under AGPLv3: "
    "https://github.com/nba1990/wcva_data_analysis"
)

# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
