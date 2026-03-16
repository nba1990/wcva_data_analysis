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
    horizontal_bar_ranked,
    kpi_card_html,
    show_chart,
    stacked_bar_ordinal,
)
from src.config import (
    DIFFICULTY_ORDER,
    WCVA_BRAND,
    AltTextConfig,
    get_app_ui_config,
    resolve_grouping,
)
from src.eda import volunteer_retention_analysis
from src.wave_context import get_wave_registry, trend_series


def render_volunteer_retention(df: pd.DataFrame, n: int) -> None:
    """Render the Volunteer Retention page: difficulty, barriers, by segment.

    Args:
        df: Filtered analysis DataFrame.
        n: Filtered row count (for chart subtitles).
    """
    """Render the Volunteer Retention page, using the current filtered dataset."""
    st.title("Volunteer Retention")

    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    ret = volunteer_retention_analysis(df)
    registry = get_wave_registry(df)
    vol_ret_trend = trend_series(
        registry,
        "workforce.headline.face_volunteer_retention_difficulties_pct",
    )

    alt_config = AltTextConfig(
        value_col="value", count_col="count", pct_col="pct", sample_size=n
    )
    cols = st.columns(3)
    cols[0].markdown(
        kpi_card_html(
            "Find retention somewhat / very difficult",
            f"{ret['pct_difficulty']}%",
            colour=WCVA_BRAND["amber"],
        ),
        unsafe_allow_html=True,
    )
    cols[1].markdown(
        kpi_card_html(
            "Report shortage retaining volunteers",
            f"{ret['pct_shortage']}%",
            colour=WCVA_BRAND["coral"],
        ),
        unsafe_allow_html=True,
    )
    cols[2].markdown(
        kpi_card_html("Organisations", str(n), colour=WCVA_BRAND["teal"]),
        unsafe_allow_html=True,
    )

    st.divider()

    # Audit trail for retention KPIs (difficulty and explicit shortage)
    with st.expander("Show how these retention KPIs are calculated"):
        vol_ret_series = df["vol_ret"]
        diff_base = int(vol_ret_series.notna().sum())
        diff_hard = int(
            vol_ret_series.isin(["Somewhat difficult", "Extremely difficult"]).sum()
        )
        if "shortage_vol_ret" in df.columns:
            shortage_series = df["shortage_vol_ret"]
            shortage_base = int(shortage_series.notna().sum())
            shortage_yes = int((shortage_series == "Yes").sum())
        else:
            shortage_base = 0
            shortage_yes = 0

        ret_rows = [
            {
                "Metric": "Find retention somewhat / very difficult",
                "Column / question": "vol_ret (Likert)",
                "Response(s) counted": "Somewhat difficult, Extremely difficult",
                "Numerator (count)": diff_hard,
                "Denominator (answered)": diff_base,
                "Percentage": ret["pct_difficulty"],
            },
            {
                "Metric": "Report shortage retaining volunteers",
                "Column / question": "shortage_vol_ret",
                "Response(s) counted": "Yes",
                "Numerator (count)": shortage_yes,
                "Denominator (answered)": shortage_base,
                "Percentage": ret["pct_shortage"],
            },
        ]
        ret_df = pd.DataFrame(ret_rows)

        st.markdown(
            "- **Retention KPIs**  \n"
            "  - The **difficulty** percentage uses only organisations that answered the Likert-scale `vol_ret` "
            "question; the base matches the **Retention Difficulty** chart on this page.  \n"
            "  - The **shortage** percentage uses the binary `shortage_vol_ret` question.  \n"
            "  - The table below shows the exact counts and bases used."
        )
        st.dataframe(ret_df, hide_index=True, width="stretch")

    st.subheader("Retention Barriers")
    fig = horizontal_bar_ranked(
        ret["ret_barriers"],
        "label",
        "count",
        "Volunteers leave for life reasons; not dissatisfaction",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(fig, "ret_barriers", ret["ret_barriers"][["label", "count", "pct"]])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("What Organisations Offer Volunteers")
        fig = horizontal_bar_ranked(
            ret["vol_offer"],
            "label",
            "count",
            "Expenses coverage leads, but financial signposting is rare",
            n,
            mode=ui_config.palette_mode,
        )
        show_chart(fig, "ret_offer", ret["vol_offer"][["label", "count", "pct"]])

    with col2:
        st.subheader("Retention Difficulty")
        grouper, group_order = resolve_grouping(DIFFICULTY_ORDER)
        TITLE = "Retention is easier than recruitment; but challenges persist"
        diff_base = int(ret["vol_ret_difficulty"]["count"].sum())
        alt_config_ret = AltTextConfig(
            value_col="value",
            count_col="count",
            pct_col="pct",
            sample_size=diff_base,
        )
        fig = stacked_bar_ordinal(
            ret["vol_ret_difficulty"],
            TITLE,
            diff_base,
            mode=ui_config.palette_mode,
            alt_config=alt_config_ret,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "ret_difficulty", ret["vol_ret_difficulty"])

    st.caption(
        f"{ret['pct_shortage']}% of organisations explicitly report a shortage retaining volunteers "
        f"(shortage_vol_ret = 'Yes'), while {ret['pct_difficulty']}% find retention somewhat or "
        "extremely difficult on the Likert scale."
    )

    if vol_ret_trend:
        earliest = vol_ret_trend[0]
        latest = vol_ret_trend[-1]
        change = latest["value"] - earliest["value"]
        direction = "higher" if change > 0 else "lower" if change < 0 else "similar"
        st.info(
            f"**Wave comparison – retention difficulty**: {earliest['value']}% in {earliest['wave_label']} "
            f"vs {latest['value']}% in {latest['wave_label']} "
            f"({abs(change)} percentage points {direction} in the latest wave)."
        )

    st.info(
        "The retention KPIs and statements are taken from the **Volunteer Retention analysis**: "
        "the difficulty tile uses the Likert-based `vol_ret` distribution, the shortage tile uses "
        "`shortage_vol_ret`, and the barriers and offers charts show the same multi-select "
        "blocks that underpin the executive summary discussion of external vs organisational factors."
    )

    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li>Executive Summary highlight #5, which notes that retention barriers are largely external, "
        "is based on the distribution of retention barriers from the `vol_ret_*` block, shown in the "
        "<strong>Retention Barriers</strong> chart above (top of this page).</li>"
        "<li>The contrast between recruitment and retention difficulty in the Executive Summary draws on "
        "the respective Likert distributions for `vol_rec` (Recruitment Difficulty chart on the Volunteer "
        "Recruitment page, top left) and `vol_ret` (Retention Difficulty chart on this page, top right).</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
