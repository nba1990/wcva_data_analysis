# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import (
    heatmap_matrix,
    horizontal_bar_ranked,
    show_chart,
    stacked_bar_ordinal,
)
from src.config import (
    DEMAND_ORDER,
    VOL_TYPEUSE_ORDER,
    WCVA_BRAND,
    AltTextConfig,
    get_app_ui_config,
    resolve_grouping,
)
from src.eda import volunteer_demographics, volunteering_types
from src.page_context import PageContext


def render_page(ctx: PageContext) -> None:
    """Standard section-page entrypoint used by src.app."""
    render_demographics_and_types(ctx.df, ctx.n)


def render_demographics_and_types(df: pd.DataFrame, n: int) -> None:
    """Render the Demographics & Types page: volunteer demographics and type usage.

    Args:
        df: Filtered analysis DataFrame.
        n: Filtered row count (for chart subtitles).
    """
    """Render the Demographics and Types page, using the current filtered dataset."""
    st.title("Volunteer Demographics & Volunteering Types")

    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    vd = volunteer_demographics(df)
    vt = volunteering_types(df)

    st.subheader("Volunteer Age/Group Presence (Last 12 Months)")
    alt_config = AltTextConfig(
        value_col="value", count_col="count", pct_col="pct", sample_size=n
    )
    fig = horizontal_bar_ranked(
        vd["dem_presence"],
        "label",
        "count",
        "26–64 age groups are the core volunteer base",
        n,
        mode=ui_config.palette_mode,
        exclude_na=False,
    )
    show_chart(fig, "dem_presence", vd["dem_presence"][["label", "count", "pct"]])

    if not vd["change_matrix"].empty:
        st.subheader("How Volunteer Numbers Changed by Group")
        change_cols = vd["change_order"]

        fig = heatmap_matrix(
            vd["change_matrix"],
            "group",
            change_cols,
            "Most groups stayed stable, with pockets of growth and decline",
            n,
            mode=ui_config.palette_mode,
            height=500,
        )

        # Collapsed - only three columns visible
        fig = heatmap_matrix(
            vd["change_matrix"],
            row_col="group",
            value_cols=[
                "Increased a lot",
                "Increased a little",
                "Stayed the same",
                "Decreased a little",
                "Decreased a lot",
                "Not applicable",
            ],
            title="Most groups stayed stable, with pockets of growth and decline",
            n=n,
            mode=ui_config.palette_mode,
            view="collapsed",  # "full" -> all columns visible, "collapsed" -> only three columns visible
        )

        show_chart(fig, "dem_change", vd["change_matrix"])

    st.divider()
    st.subheader("Change in Total Volunteer Time (Last 12 Months)")
    grouper, group_order = resolve_grouping(DEMAND_ORDER)
    fig = stacked_bar_ordinal(
        vd["vol_time"],
        "How has total volunteer time changed?",
        n,
        mode=ui_config.palette_mode,
        alt_config=alt_config,
        grouper=grouper,
        group_order=group_order,
    )
    show_chart(fig, "dem_vol_time", vd["vol_time"])

    st.divider()
    st.subheader("Types of Volunteering Used")
    for label, type_df in vt["type_data"].items():
        grouper, group_order = resolve_grouping(VOL_TYPEUSE_ORDER)
        fig = stacked_bar_ordinal(
            type_df,
            f"Types of Volunteering Used: {label}",
            n,
            mode=ui_config.palette_mode,
            height=140,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, f"type_{label.replace(' ', '_')}", type_df)

    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li>Comments in the Executive Summary about who is volunteering (for example, age groups forming "
        "the core volunteer base) are supported by the `vol_dem_*` multi-select block shown in the "
        "<strong>Volunteer Age/Group Presence</strong> chart (top of this page) and the `vol_dem_change_*` "
        "columns visualised in the heatmap below.</li>"
        "<li>Any references to the mix of volunteering types (e.g. micro, virtual, remote) draw on the "
        "`vol_typeuse_*` columns displayed in the series of <strong>Types of Volunteering Used</strong> "
        "stacked bar charts along the bottom of this page.</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
