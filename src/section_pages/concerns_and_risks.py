# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import horizontal_bar_ranked, kpi_card_html, show_chart, wave_trend_line
from src.config import WCVA_BRAND, get_app_ui_config
from src.eda import workforce_operations
from src.wave_context import (
    build_trend_long,
    build_trend_pivot,
    get_wave_registry,
    summarise_trend_changes,
)


def render_concerns_and_risks(df: pd.DataFrame, n: int) -> None:
    """Render the Concerns & Risks page: key concerns, actions, reserves, and narrative.

    Args:
        df: Filtered analysis DataFrame.
        n: Filtered row count (for chart subtitles).
    """
    """Render the Concerns and Risks page, using the current filtered dataset."""
    st.title("Organisational Concerns & Risks")

    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    wf = workforce_operations(df)

    st.markdown(
        "This page shows the full distributions behind the executive summary statements "
        "about income, increasing demand, recruitment and retention concerns, and the "
        "operational impact of rising costs and shortages."
    )

    # Top three concerns as headline cards (matches reference top-cards style)
    if not wf["concerns"].empty:
        top_concerns = wf["concerns"].head(3).reset_index(drop=True)
        card_cols = st.columns(len(top_concerns))
        for idx, row in top_concerns.iterrows():
            label = str(row["label"])
            pct = row["pct"]
            card_cols[idx].markdown(
                kpi_card_html(
                    label,
                    f"{pct}%",
                    colour=WCVA_BRAND["amber"] if idx == 0 else WCVA_BRAND["teal"],
                ),
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Operational Concerns (current wave / filtered view)")
    fig = horizontal_bar_ranked(
        wf["concerns"],
        "label",
        "count",
        "Concerns organisations highlight as most pressing",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(fig, "concerns_full", wf["concerns"][["label", "count", "pct"]])

    st.info(
        "The executive summary headline **“Income is the #1 concern”** and references to "
        "**increasing demand as the second most common concern** are derived directly from "
        "the ordering and percentages in the chart and table above."
    )

    st.divider()
    st.subheader("Concerns as Top Issues Across Waves")
    registry = get_wave_registry(df)

    trend_df = build_trend_long(registry)
    concern_ids = ["income_top_concern", "demand_top_concern", "inflation_top_concern"]
    concerns_trend = trend_df[trend_df["metric_id"].isin(concern_ids)].copy()

    if concerns_trend.empty:
        st.info(
            "No cross-wave concerns metrics are available yet. Add them to TREND_METRICS to enable this view."
        )
    else:
        wide_concerns = build_trend_pivot(concerns_trend)
        st.dataframe(wide_concerns, hide_index=True, width="stretch")

        summaries = summarise_trend_changes(concerns_trend, concern_ids)
        if summaries:
            bullets = []
            for mid in concern_ids:
                summary = summaries.get(mid)
                if not summary:
                    continue
                direction = (
                    "increased"
                    if summary["change_pct_points"] > 0
                    else (
                        "decreased"
                        if summary["change_pct_points"] < 0
                        else "was unchanged"
                    )
                )
                bullets.append(
                    f"- **{summary['label']}** {direction} from {summary['first_value']}% in {summary['first_wave']} "
                    f"to {summary['latest_value']}% in {summary['latest_wave']} "
                    f"({summary['change_pct_points']} percentage points)."
                )
            if bullets:
                st.markdown("#### Cross-wave concern story")
                st.markdown("\n".join(bullets))

        st.markdown("#### Concern trends by theme")
        for metric_label, mdf in concerns_trend.groupby("metric_label"):
            mdf = mdf.sort_values("wave_number")
            fig_line = wave_trend_line(
                mdf,
                metric_label,
                mode=ui_config.palette_mode,
            )
            show_chart(
                fig_line,
                key=f"concerns_trend_{metric_label}",
                data_df=mdf[["wave_label", "wave_number", "wave_n", "value"]],
            )

    st.divider()
    st.subheader("Actions Taken Due to Rising Costs")
    fig = horizontal_bar_ranked(
        wf["actions"],
        "label",
        "count",
        "How organisations have responded to rising costs",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(fig, "concerns_actions", wf["actions"][["label", "count", "pct"]])

    st.info(
        "The executive summary highlight about **unplanned use of reserves** comes from the "
        "row labelled “Unplanned use of reserves” in the actions table above."
    )

    st.divider()
    st.subheader("Operational Impact of Shortages")
    fig = horizontal_bar_ranked(
        wf["shortage_affect"],
        "label",
        "count",
        "Consequences organisations report from staff or volunteer shortages",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(
        fig,
        "concerns_shortage_affect",
        wf["shortage_affect"][["label", "count", "pct"]],
    )

    st.divider()
    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li><strong>Headline #1 (Income is the #1 concern)</strong> is based on the highest "
        "percentage row in the <strong>Operational Concerns</strong> chart above, which is built from the "
        "`concerns_*` multi-select block and summarised in `workforce_operations`.</li>"
        "<li><strong>References to increasing demand as a major concern</strong> use the "
        "“Increasing demand” row in that same concerns chart together with the cross-wave concern trends "
        "for metric IDs such as `demand_top_concern`.</li>"
        "<li><strong>Highlights about rising costs and reserves</strong> draw on both the "
        "actions table (especially the row where `actions_*` maps to “Unplanned use of reserves”) and the "
        "reserves KPIs (`reserves_yes_pct`, `using_reserves_pct`) on the Workforce & Operations page.</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
