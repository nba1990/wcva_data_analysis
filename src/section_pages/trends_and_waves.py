# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import show_chart, wave_trend_line
from src.config import MAX_ROWS_STREAMLIT_UI, WCVA_BRAND, get_app_ui_config
from src.eda import volunteer_recruitment_analysis, workforce_operations
from src.page_context import PageContext
from src.wave_context import (
    build_trend_long,
    build_trend_pivot,
    get_wave_registry,
    summarise_trend_changes,
)


def render_page(ctx: PageContext) -> None:
    """Standard section-page entrypoint used by src.app."""
    render_trends_and_waves(ctx.df)


def render_trends_and_waves(df: pd.DataFrame) -> None:
    """Render the Trends & Waves page: cross-wave comparison and trend charts.

    Args:
        df: Filtered analysis DataFrame (used to build wave registry and trend data).
    """
    """Render the Trends and Waves page, using the current filtered dataset."""
    st.title("Trends Across Waves")
    st.caption(
        "Compare headline indicators across survey waves using the validated WaveContext model."
    )

    ui_config = get_app_ui_config()
    registry = get_wave_registry(df)

    trend_df = build_trend_long(registry)

    if trend_df.empty:
        st.info(
            "No cross-wave metrics are available yet. Add more waves or metrics to TREND_METRICS."
        )
        st.stop()
    # Narrative summary for key metrics using earliest vs latest change
    key_metric_ids = [
        "demand_increase",
        "finance_deteriorated_costs",
        "too_few_volunteers",
        "has_reserves",
        "using_reserves",
    ]
    summaries = summarise_trend_changes(trend_df, key_metric_ids)
    if summaries:
        lines = []
        for mid in key_metric_ids:
            summary = summaries.get(mid)
            if not summary:
                continue
            direction = (
                "increased"
                if summary["change_pct_points"] > 0
                else (
                    "decreased" if summary["change_pct_points"] < 0 else "was unchanged"
                )
            )
            lines.append(
                f"- **{summary['label']}** {direction} from {summary['first_value']}% in {summary['first_wave']} "
                f"to {summary['latest_value']}% in {summary['latest_wave']} "
                f"({summary['change_pct_points']} percentage points)."
            )
        if lines:
            st.subheader("Headline cross-wave story")
            st.markdown("\n".join(lines))
            st.divider()

    # Metric selection / filtering
    st.sidebar.subheader("Trend metrics")
    available_labels = sorted(trend_df["metric_label"].unique().tolist())
    selected_labels = st.sidebar.multiselect(
        "Select metrics to display",
        options=available_labels,
        default=available_labels,
    )

    working_df = trend_df[trend_df["metric_label"].isin(selected_labels)].copy()

    st.subheader("Headline trend table")
    wide = build_trend_pivot(working_df)
    max_rows = MAX_ROWS_STREAMLIT_UI
    display_wide = wide.head(max_rows)
    st.dataframe(display_wide, hide_index=True, width="stretch")
    if len(wide) > max_rows:
        st.caption(
            f"Showing first {max_rows} rows. Download the full table as CSV for offline analysis."
        )

    # Download full long-format trends as CSV for external analysis
    csv = trend_df.to_csv(index=False)
    st.download_button(
        "Download trends CSV",
        csv,
        file_name="wave_trends_long.csv",
        mime="text/csv",
        key="download_trends_csv",
    )

    st.divider()
    st.subheader("Trend charts by theme")

    for section_name, section_df in working_df.groupby("section"):
        st.markdown(f"### {section_name}")

        # Group metrics within this section into two-column layout
        metric_groups = list(section_df.groupby("metric_label"))
        cols = st.columns(2)

        for idx, (metric_label, mdf) in enumerate(metric_groups):
            col = cols[idx % 2]
            with col:
                mdf = mdf.sort_values("wave_number")

                fig = wave_trend_line(
                    mdf,
                    metric_label,
                    mode=ui_config.palette_mode,
                )

                show_chart(
                    fig,
                    key=f"trend_{section_name}_{metric_label}",
                    data_df=mdf[["wave_label", "wave_number", "wave_n", "value"]],
                )

    # Static Wave 1 income & expenditure breakdown (non-interactive benchmark)
    st.divider()
    st.subheader("Wave 1 income and expenditure breakdown (static benchmark)")
    wave1_ctx = registry.get("Wave 1")
    with st.expander("Show Wave 1 income and expenditure tables (unfiltered)"):
        income_sources = pd.DataFrame(
            list(wave1_ctx.finance.income_breakdown.sources_pct.items()),
            columns=["Income source", "Percent of organisations"],
        ).sort_values("Percent of organisations", ascending=False)
        st.markdown("**Income by funding source (Wave 1)**")
        st.dataframe(income_sources, hide_index=True, width="stretch")

        exp_categories = pd.DataFrame(
            list(wave1_ctx.finance.expenditure_breakdown.categories_pct.items()),
            columns=["Cost category", "Percent of expenditure"],
        ).sort_values("Percent of expenditure", ascending=False)
        st.markdown("**Expenditure by cost category (Wave 1)**")
        st.dataframe(exp_categories, hide_index=True, width="stretch")

    st.divider()
    st.subheader("Debug: EDA vs WaveContext (Wave 2)")

    with st.expander("Show comparison table for key metrics"):
        if "Wave 2" not in registry.waves:
            st.info(
                "Wave 2 context is not available for the current dataset "
                "(for example, because there are too few responses). "
                "Cross-wave debug comparisons are skipped."
            )
        else:
            rec = volunteer_recruitment_analysis(df)
            wf = workforce_operations(df)

            wave2_ctx = registry.get("Wave 2")

            debug_rows = [
                {
                    "metric": "Too few volunteers %",
                    "source": "EDA (pct_too_few)",
                    "value": rec["pct_too_few"],
                },
                {
                    "metric": "Too few volunteers %",
                    "source": "WaveContext (workforce.headline.too_few_volunteers_pct)",
                    "value": wave2_ctx.workforce.headline.too_few_volunteers_pct,
                },
                {
                    "metric": "Has reserves %",
                    "source": "EDA (reserves_yes_pct)",
                    "value": wf["reserves_yes_pct"],
                },
                {
                    "metric": "Has reserves %",
                    "source": "WaveContext (headline_kpis.financial_health.has_financial_reserves_pct)",
                    "value": wave2_ctx.headline_kpis.financial_health.has_financial_reserves_pct,
                },
                {
                    "metric": "Using reserves (of those with reserves) %",
                    "source": "EDA (using_reserves_pct)",
                    "value": wf["using_reserves_pct"],
                },
                {
                    "metric": "Using reserves (of those with reserves) %",
                    "source": "WaveContext (headline_kpis.financial_health.using_reserves_among_those_with_reserves_pct)",
                    "value": wave2_ctx.headline_kpis.financial_health.using_reserves_among_those_with_reserves_pct,
                },
            ]

            debug_df = pd.DataFrame(debug_rows)

            # Add a simple match flag (EDA vs WaveContext) within each metric
            tolerance = 0.5  # allowed absolute difference for rounding
            debug_df["match"] = ""
            for metric_name in debug_df["metric"].unique():
                subset = debug_df[debug_df["metric"] == metric_name]
                if len(subset) == 2:
                    v1, v2 = subset["value"].iloc[0], subset["value"].iloc[1]
                    ok = abs(float(v1) - float(v2)) <= tolerance
                    debug_df.loc[subset.index, "match"] = ok
            st.dataframe(debug_df, hide_index=True, width="stretch")
            st.caption(
                "EDA aggregates and WaveContext values should match (aside from integer rounding). "
                "The 'match' column shows whether values agree within a small tolerance; "
                "if it is False, it indicates a mapping or transformation issue."
            )

    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li>All cross-wave statements in the Executive Summary (for example, comparisons between Wave 1 "
        "and Wave 2 on demand, finances, reserves and volunteer gaps) are drawn from the trend table and "
        "line charts on this page, which in turn are built from the WaveContext registry columns such as "
        "`demand_increase`, `finance_deteriorated_costs`, `too_few_volunteers`, `has_reserves` and "
        "`using_reserves`.</li>"
        "<li>The debug table at the bottom links EDA aggregates like `pct_too_few` and `reserves_yes_pct` "
        "to their WaveContext counterparts, providing a direct audit trail for the Executive Summary metrics.</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
