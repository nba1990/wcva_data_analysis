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
    grouped_bar,
    horizontal_bar_ranked,
    kpi_card_html,
    show_chart,
    stacked_bar_ordinal,
)
from src.config import (
    DIFFICULTY_ORDER,
    ORG_SIZE_ORDER,
    VOL_OBJECTIVES_ORDER,
    WCVA_BRAND,
    AltTextConfig,
    get_app_ui_config,
    resolve_grouping,
)
from src.eda import volunteer_recruitment_analysis, volunteer_retention_analysis
from src.narratives import recruitment_vs_retention_phrase
from src.page_context import PageContext
from src.wave_context import get_wave_registry, trend_series


def render_page(ctx: PageContext) -> None:
    """Standard section-page entrypoint used by src.app."""
    render_volunteer_recruitment(ctx.df, ctx.n)


def render_volunteer_recruitment(df: pd.DataFrame, n: int) -> None:
    """Render the Volunteer Recruitment page: difficulty, barriers, methods, by segment.

    Args:
        df: Filtered analysis DataFrame.
        n: Filtered row count (for chart subtitles).
    """
    """Render the Volunteer Recruitment page, using the current filtered dataset."""
    st.title("Volunteer Recruitment")

    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    rec = volunteer_recruitment_analysis(df)
    # Cross-wave context for recruitment difficulty
    registry = get_wave_registry(df)
    vol_rec_trend = trend_series(
        registry,
        "workforce.headline.face_volunteer_recruitment_difficulties_pct",
    )

    cols = st.columns(3)
    cols[0].markdown(
        kpi_card_html(
            "Find recruitment somewhat / very difficult",
            f"{rec['pct_difficulty']}%",
            colour=WCVA_BRAND["coral"],
        ),
        unsafe_allow_html=True,
    )
    cols[1].markdown(
        kpi_card_html(
            "Report shortage recruiting volunteers",
            f"{rec['pct_shortage']}%",
            colour=WCVA_BRAND["amber"],
        ),
        unsafe_allow_html=True,
    )
    cols[2].markdown(
        kpi_card_html("Organisations", str(n), colour=WCVA_BRAND["teal"]),
        unsafe_allow_html=True,
    )

    st.divider()

    # Audit trail for recruitment KPIs (difficulty and explicit shortage)
    with st.expander("Show how these recruitment KPIs are calculated"):
        # Difficulty: Likert-based, non-missing vol_rec base
        vol_rec_series = df["vol_rec"]
        diff_base = int(vol_rec_series.notna().sum())
        diff_hard = int(
            vol_rec_series.isin(["Somewhat difficult", "Extremely difficult"]).sum()
        )
        # Explicit shortage: shortage_vol_rec True among those with a recorded value
        if "shortage_vol_rec" in df.columns:
            shortage_series = df["shortage_vol_rec"]
            shortage_base = int(shortage_series.notna().sum())
            shortage_yes = int((shortage_series == "Yes").sum())
        else:
            shortage_base = 0
            shortage_yes = 0

        rec_rows = [
            {
                "Metric": "Find recruitment somewhat / very difficult",
                "Column / question": "vol_rec (Likert)",
                "Response(s) counted": "Somewhat difficult, Extremely difficult",
                "Numerator (count)": diff_hard,
                "Denominator (answered)": diff_base,
                "Percentage": rec["pct_difficulty"],
            },
            {
                "Metric": "Report shortage recruiting volunteers",
                "Column / question": "shortage_vol_rec",
                "Response(s) counted": "Yes",
                "Numerator (count)": shortage_yes,
                "Denominator (answered)": shortage_base,
                "Percentage": rec["pct_shortage"],
            },
        ]
        rec_df = pd.DataFrame(rec_rows)

        st.markdown(
            "- **Recruitment KPIs**  \n"
            "  - The **difficulty** percentage uses only organisations that answered the Likert-scale `vol_rec` "
            "question; the base matches the **Recruitment Difficulty** chart.  \n"
            "  - The **shortage** percentage uses the binary `shortage_vol_rec` question, with its own non-missing "
            "base.  \n"
            "  - The table below shows the exact counts and bases used."
        )
        st.dataframe(rec_df, hide_index=True, width="stretch")
    alt_config = AltTextConfig(
        value_col="value", count_col="count", pct_col="pct", sample_size=n
    )
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Recruitment Difficulty")
        grouper, group_order = resolve_grouping(DIFFICULTY_ORDER)
        TITLE = "Most organisations find recruitment somewhat or extremely difficult"
        # Use the number answering this question (non-missing) as the base for alt text
        diff_base = int(rec["vol_rec_difficulty"]["count"].sum())
        alt_config_diff = AltTextConfig(
            value_col="value",
            count_col="count",
            pct_col="pct",
            sample_size=diff_base,
        )
        fig = stacked_bar_ordinal(
            rec["vol_rec_difficulty"],
            TITLE,
            diff_base,
            mode=ui_config.palette_mode,
            alt_config=alt_config_diff,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "rec_difficulty", rec["vol_rec_difficulty"])

        # Explain the two metrics and how recruitment compares to retention overall
        ret_summary = volunteer_retention_analysis(df)
        comparison_sentence = recruitment_vs_retention_phrase(rec, ret_summary)
        st.caption(
            f"{rec['pct_shortage']}% of organisations explicitly report a shortage recruiting volunteers "
            f"(shortage_vol_rec = 'Yes'), while {rec['pct_difficulty']}% of those answering the difficulty "
            "question find recruitment somewhat or extremely difficult on the Likert scale. "
            + comparison_sentence
        )

    with col2:
        st.subheader("Volunteer Numbers vs. Need")
        grouper, group_order = resolve_grouping(VOL_OBJECTIVES_ORDER)
        TITLE = "Majority report having too few volunteers for their objectives"
        obj_base = int(rec["vol_objectives"]["count"].sum())
        alt_config_obj = AltTextConfig(
            value_col="value",
            count_col="count",
            pct_col="pct",
            sample_size=obj_base,
        )
        fig = stacked_bar_ordinal(
            rec["vol_objectives"],
            TITLE,
            obj_base,
            mode=ui_config.palette_mode,
            alt_config=alt_config_obj,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "rec_objectives", rec["vol_objectives"])

    st.subheader("Top Recruitment Methods Used")
    fig = horizontal_bar_ranked(
        rec["rec_methods"],
        "label",
        "count",
        "Word of mouth dominates, but digital channels are close behind",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(fig, "rec_methods", rec["rec_methods"][["label", "count", "pct"]])

    st.subheader("Top Barriers to Recruitment")
    fig = horizontal_bar_ranked(
        rec["rec_barriers"],
        "label",
        "count",
        "The problem isn't lack of effort. It's low response and limited capacity",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(fig, "rec_barriers", rec["rec_barriers"][["label", "count", "pct"]])

    if (
        "Large" in rec["rec_barriers_by_size"].columns
        and "Small" in rec["rec_barriers_by_size"].columns
    ):
        st.subheader("Barriers by Organisation Size")
        seg_cols = [
            c for c in ORG_SIZE_ORDER if c in rec["rec_barriers_by_size"].columns
        ]
        fig = grouped_bar(
            rec["rec_barriers_by_size"],
            "label",
            seg_cols,
            "How barriers differ by organisation size",
            n,
            mode=ui_config.palette_mode,
        )
        show_chart(fig, "rec_barriers_seg", rec["rec_barriers_by_size"])

    if vol_rec_trend:
        earliest = vol_rec_trend[0]
        latest = vol_rec_trend[-1]
        change = latest["value"] - earliest["value"]
        direction = "higher" if change > 0 else "lower" if change < 0 else "similar"
        st.info(
            f"**Wave comparison – recruitment difficulty**: {earliest['value']}% in {earliest['wave_label']} "
            f"vs {latest['value']}% in {latest['wave_label']} "
            f"({abs(change)} percentage points {direction} in the latest wave)."
        )

    st.info(
        "The recruitment KPIs and narrative in this page are based on the **Volunteer Recruitment "
        "analysis**: the difficulty tiles use the Likert-scale `vol_rec` distribution, the shortage "
        "tile uses `shortage_vol_rec`, and the “too few volunteers” figures come from the "
        "`volobjectives` distribution shown in the 'Volunteer Numbers vs. Need' chart."
    )

    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li>Executive Summary highlight #3 on organisations having too few volunteers and "
        "finding recruitment difficult is drawn from the `vol_rec` <strong>Recruitment Difficulty</strong> chart (top left) "
        "and the `volobjectives` <strong>Volunteer Numbers vs. Need</strong> chart (top right) respectively, and from the "
        "underlying distributions presented on this page.</li>"
        "<li>The discussion of recruitment methods and barriers (highlight #4) is backed by the "
        "multi-select charts here on this page for recruitment methods and barriers.</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
