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
from typing import Callable

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
from src.page_context import PageContext
from src.section_pages import (
    at_a_glance,
    concerns_and_risks,
    data_notes,
    demographics_and_types,
    deployment_health,
    earned_settlement,
    executive_summary,
    overview,
    sroi_references,
    trends_and_waves,
    volunteer_recruitment,
    volunteer_retention,
    workforce_and_operations,
)

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


try:
    df_full, dataset_source = get_data()
except (FileNotFoundError, RuntimeError) as exc:
    st.error(
        "The Wave 2 dataset could not be loaded.\n\n"
        "Details:\n\n"
        f"{exc}\n\n"
        "Check your dataset paths/URLs or secrets configuration, then "
        "refresh the app. You can also use the Deployment Health page to "
        "see which runtime files are missing."
    )
    st.stop()

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

from src.filters import apply_filters

df = apply_filters(df_full, ui_config)

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

ctx = PageContext(
    df=df,
    df_full=df_full,
    n=n,
    ui_config=ui_config,
    prof=prof,
    asset_report=asset_report,
)

PAGE_RENDERERS: dict[str, Callable] = {
    "At-a-Glance": at_a_glance.render_page,
    "Overview": overview.render_page,
    "Volunteer Recruitment": volunteer_recruitment.render_page,
    "Volunteer Retention": volunteer_retention.render_page,
    "Trends & Waves": trends_and_waves.render_page,
    "Workforce & Operations": workforce_and_operations.render_page,
    "Concerns & Risks": concerns_and_risks.render_page,
    "Demographics & Types": demographics_and_types.render_page,
    "Earned Settlement": earned_settlement.render_page,
    "Executive Summary": executive_summary.render_page,
    "SROI & References": sroi_references.render_page,
    "Deployment Health": deployment_health.render_page,
    "Data Notes": data_notes.render_page,
}


def _run_page(page_id: str, context: PageContext) -> None:
    """Render a page with a small error boundary.

    This keeps navigation and filters usable even if a single page fails.
    """
    renderer = PAGE_RENDERERS.get(page_id)
    if renderer is None:
        st.error(
            f"Unknown page ID: {page_id!r}. "
            "Check NAV_ITEMS in src.navigation and PAGE_RENDERERS in src.app."
        )
        return

    try:
        renderer(context)
    except Exception as exc:  # pragma: no cover - defensive boundary
        st.error(
            "An unexpected error occurred while rendering this page.\n\n"
            "You can:\n"
            "- Try a different page from the sidebar.\n"
            "- Review the Deployment Health page to check runtime assets.\n"
            "- Check server logs for the full traceback if you maintain this deployment."
        )
        # Still surface the exception in Streamlit's logs for debugging.
        st.exception(exc)


_run_page(page, ctx)


# ---------------------------------------------------------------------------
# Global footer (shown on every page)
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Source code available under AGPLv3: "
    "https://github.com/nba1990/wcva_data_analysis"
)

# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
