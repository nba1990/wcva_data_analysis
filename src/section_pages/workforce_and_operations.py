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
    WCVA_BRAND,
    YES_NO_ORDER,
    AltTextConfig,
    get_app_ui_config,
    resolve_grouping,
)
from src.eda import workforce_operations
from src.wave_context import get_wave_registry, trend_series


def render_workforce_and_operations(df: pd.DataFrame, n: int) -> None:
    """Render the Workforce & Operations page: staff/vol recruitment and retention, concerns, actions.

    Args:
        df: Filtered analysis DataFrame.
        n: Filtered row count (for chart subtitles).
    """
    """Render the Workforce and Operations page, using the current filtered dataset."""
    st.title("Workforce & Operations")

    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    wf = workforce_operations(df)
    registry = get_wave_registry(df)
    staff_rec_trend = trend_series(
        registry,
        "workforce.headline.face_staff_recruitment_difficulties_pct",
    )

    cols = st.columns(4)
    cols[0].markdown(
        kpi_card_html(
            "Finances deteriorated due to rising costs",
            f"{wf['finance_deteriorated_pct']}%",
            colour=WCVA_BRAND["coral"],
        ),
        unsafe_allow_html=True,
    )
    cols[1].markdown(
        kpi_card_html(
            "Have reserves", f"{wf['reserves_yes_pct']}%", colour=WCVA_BRAND["teal"]
        ),
        unsafe_allow_html=True,
    )
    cols[2].markdown(
        kpi_card_html(
            "Using reserves",
            f"{wf['using_reserves_pct']}%",
            delta="of those with reserves",
            colour=WCVA_BRAND["amber"],
        ),
        unsafe_allow_html=True,
    )
    cols[3].markdown(
        kpi_card_html(
            "Median reserves",
            (
                f"{wf['median_months_reserves']:.0f} months"
                if pd.notna(wf["median_months_reserves"])
                else "N/A"
            ),
            colour=WCVA_BRAND["blue"],
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    # Audit trail for finance & reserves KPIs on this page
    with st.expander("Show how these finance and reserves KPIs are calculated"):
        st.caption(
            'Note: "Finances deteriorated due to rising costs" (below) uses a different question from '
            '"Financial position deteriorated (last 3 months)" on the Overview and At-a-Glance pages; both are valid.'
        )
        finance_series = df.get("financedeteriorate")
        if finance_series is not None:
            finance_base = int(finance_series.notna().sum())
            finance_yes = int((finance_series == "Yes").sum())
        else:
            finance_base = 0
            finance_yes = 0

        reserves_series = df.get("reserves")
        if reserves_series is not None:
            reserves_base = int(reserves_series.notna().sum())
            reserves_yes = int((reserves_series == "Yes").sum())
        else:
            reserves_base = 0
            reserves_yes = 0

        # Using reserves is recorded in the same way as the EDA function:
        # column name `usingreserves`, with the percentage calculated among
        # organisations that have reserves (`reserves == "Yes"`).
        using_reserves_series = df.get("usingreserves")
        if using_reserves_series is not None and reserves_series is not None:
            has_reserves_mask = reserves_series == "Yes"
            using_base_with_reserves = int(has_reserves_mask.sum())
            using_answered_base = int(using_reserves_series.notna().sum())
            using_yes = int(using_reserves_series[has_reserves_mask].eq("Yes").sum())
        else:
            using_base_with_reserves = 0
            using_answered_base = 0
            using_yes = 0

        # Use consistent types for Arrow serialization: "Denominator (with reserves)"
        # is string (empty or numeric string) so st.dataframe does not mix int and str.
        wf_rows = [
            {
                "Metric": "Finances deteriorated due to rising costs",
                "Column / question": "financedeteriorate",
                "Response(s) counted": "Yes",
                "Numerator (count)": finance_yes,
                "Denominator (answered)": finance_base,
                "Denominator (with reserves)": "",  # N/A for this metric
                "Percentage": wf["finance_deteriorated_pct"],
            },
            {
                "Metric": "Have reserves",
                "Column / question": "reserves",
                "Response(s) counted": "Yes",
                "Numerator (count)": reserves_yes,
                "Denominator (answered)": reserves_base,
                "Denominator (with reserves)": "",  # N/A for this metric
                "Percentage": wf["reserves_yes_pct"],
            },
            {
                "Metric": "Using reserves (of those with reserves)",
                "Column / question": "usingreserves",
                "Response(s) counted": "Yes (among reserves == 'Yes')",
                "Numerator (count)": using_yes,
                "Denominator (answered)": using_answered_base,
                "Denominator (with reserves)": str(using_base_with_reserves),
                "Percentage": wf["using_reserves_pct"],
            },
        ]
        wf_df = pd.DataFrame(wf_rows)

        st.markdown(
            "- **Finance and reserves KPIs**  \n"
            "  - These percentages are calculated directly from the `financedeteriorate`, `reserves` and "
            "`using_reserves` questions that also underpin the **Actions Taken Due to Rising Costs** chart and "
            "the executive summary finance highlights.  \n"
            "  - The table shows the exact counts and bases used for each tile."
        )
        st.dataframe(wf_df, hide_index=True, width="stretch")

    st.subheader("Top 3 Concerns")
    fig = horizontal_bar_ranked(
        wf["concerns"],
        "label",
        "count",
        "Income dominates concerns, with demand and volunteer recruitment close behind",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(fig, "wf_concerns", wf["concerns"][["label", "count", "pct"]])

    st.subheader("Actions Taken Due to Rising Costs")
    fig = horizontal_bar_ranked(
        wf["actions"],
        "label",
        "count",
        "Price increases and unplanned reserves usage are the most common responses",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(fig, "wf_actions", wf["actions"][["label", "count", "pct"]])

    st.divider()
    st.subheader("Impact of Shortages")
    fig = horizontal_bar_ranked(
        wf["shortage_affect"],
        "label",
        "count",
        "Unable to meet demand and paused operations are the most common consequences",
        n,
        mode=ui_config.palette_mode,
    )
    show_chart(
        fig, "wf_shortage_affect", wf["shortage_affect"][["label", "count", "pct"]]
    )

    st.divider()
    st.subheader("Staff Recruitment & Retention Difficulty")
    alt_config_wf = AltTextConfig(
        value_col="value",
        count_col="count",
        pct_col="pct",
        sample_size=wf["n_with_staff"],
    )
    col_sr, col_sret = st.columns(2)
    with col_sr:
        grouper, group_order = resolve_grouping(YES_NO_ORDER)
        fig = stacked_bar_ordinal(
            wf["staff_rec_difficulty"],
            f"Staff recruitment difficulty (n={wf['n_with_staff']} with paid staff)",
            wf["n_with_staff"],
            mode=ui_config.palette_mode,
            alt_config=alt_config_wf,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "wf_staff_rec", wf["staff_rec_difficulty"])
    with col_sret:
        fig = stacked_bar_ordinal(
            wf["staff_ret_difficulty"],
            f"Staff retention difficulty (n={wf['n_with_staff']} with paid staff)",
            wf["n_with_staff"],
            mode=ui_config.palette_mode,
            alt_config=alt_config_wf,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "wf_staff_ret", wf["staff_ret_difficulty"])

    if staff_rec_trend:
        earliest = staff_rec_trend[0]
        latest = staff_rec_trend[-1]
        change = latest["value"] - earliest["value"]
        direction = "higher" if change > 0 else "lower" if change < 0 else "similar"
        st.info(
            f"**Wave comparison – staff recruitment difficulty**: {earliest['value']}% in {earliest['wave_label']} "
            f"vs {latest['value']}% in {latest['wave_label']} "
            f"({abs(change)} percentage points {direction} in the latest wave)."
        )

    st.info(
        "The workforce KPIs and concerns in this page are driven by the **Workforce & Operations analysis** "
        "(`workforce_operations`): the finance and reserves tiles come from the same aggregates that feed the "
        "executive summary and cross-wave trends, while the concerns, actions, and shortage-impact charts "
        "mirror the detailed breakdowns on the **Concerns & Risks** page."
    )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
