from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.charts import (
    donut_chart,
    horizontal_bar_ranked,
    kpi_card_html,
    show_chart,
    stacked_bar_ordinal,
)
from src.config import (
    DEMAND_ORDER,
    EXPECT_DEMAND_ORDER,
    EXPECT_FINANCIAL_ORDER,
    FINANCIAL_ORDER,
    OPERATING_ORDER,
    WCVA_BRAND,
    AltTextConfig,
    resolve_grouping,
)
from src.eda import (
    demand_and_outlook,
    volunteer_recruitment_analysis,
    volunteer_retention_analysis,
    workforce_operations,
)
from src.narratives import demand_finance_scissor_phrase
from src.wave_context import get_wave_registry


def render_overview(
    df: pd.DataFrame,
    *,
    suppressed: bool,
    n: int,
    palette_mode: str,
    prof: dict[str, Any],
) -> None:
    """Render the Overview page: profile, demand/finance/operating charts, narratives.

    Args:
        df: Filtered analysis DataFrame.
        suppressed: If True, show suppression warning (n < K_ANON_THRESHOLD).
        n: Filtered row count.
        palette_mode: "brand" or "accessible" for chart colours.
        prof: Result of profile_summary(df) for profile section.
    """
    st.title("Baromedr Cymru Wave 2 — Overview")

    if suppressed:
        st.warning(
            "Results suppressed due to small sample size. Adjust filters to see data."
        )
        st.stop()

    dem = demand_and_outlook(df)
    wf_overview = workforce_operations(df)
    rec_overview = volunteer_recruitment_analysis(df)
    ret_overview = volunteer_retention_analysis(df)

    cols = st.columns(4)
    cols[0].markdown(
        kpi_card_html("Organisations", str(n), colour=WCVA_BRAND["teal"]),
        unsafe_allow_html=True,
    )
    cols[1].markdown(
        kpi_card_html(
            "Demand increasing",
            f"{dem['demand_pct_increased']}%",
            colour=WCVA_BRAND["amber"],
        ),
        unsafe_allow_html=True,
    )
    cols[2].markdown(
        kpi_card_html(
            "Financial position deteriorated (last 3 months)",
            f"{dem['financial_pct_deteriorated']}%",
            colour=WCVA_BRAND["coral"],
        ),
        unsafe_allow_html=True,
    )
    cols[3].markdown(
        kpi_card_html(
            "Likely operating next yr",
            f"{dem['operating_pct_likely']}%",
            colour=WCVA_BRAND["teal"],
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    # Explicit audit trail for the headline Overview KPIs
    with st.expander("Show how these overview KPIs are calculated"):
        demand_inc_count = int(df["demand_direction"].eq("Increased").sum())
        demand_base = int(df["demand_direction"].notna().sum())
        finance_det_count = int(df["financial_direction"].eq("Deteriorated").sum())
        finance_base = int(df["financial_direction"].notna().sum())
        operating_likely_count = int(
            df["operating"].isin(["Very likely", "Quite likely"]).sum()
        )
        operating_base = int(df["operating"].notna().sum())

        overview_rows = [
            {
                "Metric": "Demand increasing",
                "Column / question": "demand_direction",
                "Numerator (count)": demand_inc_count,
                "Denominator (answered)": demand_base,
                "Percentage": dem["demand_pct_increased"],
            },
            {
                "Metric": "Financial position deteriorated (last 3 months)",
                "Column / question": "financial_direction",
                "Numerator (count)": finance_det_count,
                "Denominator (answered)": finance_base,
                "Percentage": dem["financial_pct_deteriorated"],
            },
            {
                "Metric": "Likely operating next yr",
                "Column / question": "operating",
                "Numerator (count)": operating_likely_count,
                "Denominator (answered)": operating_base,
                "Percentage": dem["operating_pct_likely"],
            },
        ]
        overview_df = pd.DataFrame(overview_rows)

        st.markdown(
            "- **Overview headline KPIs**  \n"
            "  - These tiles use the same non-missing base as the stacked bar charts in the **Recent Experience** "
            "and **Looking Ahead** sections below.  \n"
            "  - The table shows the exact counts and bases used for each percentage."
        )
        st.dataframe(overview_df, hide_index=True, width="stretch")

    # Workforce coverage headline row (aligned with WaveContext.WorkforceHeadline)
    st.divider()
    st.subheader("Workforce coverage at a glance")
    wc_cols = st.columns(3)
    prof_wc = prof
    wc_cols[0].markdown(
        kpi_card_html(
            "Has volunteers",
            f"{prof_wc['has_volunteers_pct']}%",
            colour=WCVA_BRAND["green"],
        ),
        unsafe_allow_html=True,
    )
    wc_cols[1].markdown(
        kpi_card_html(
            "Has paid staff",
            f"{prof_wc['has_paid_staff_pct']}%",
            colour=WCVA_BRAND["teal"],
        ),
        unsafe_allow_html=True,
    )
    wc_cols[2].markdown(
        kpi_card_html(
            "Too few volunteers",
            f"{rec_overview['pct_too_few']}%",
            colour=WCVA_BRAND["coral"],
        ),
        unsafe_allow_html=True,
    )

    wc_cols2 = st.columns(3)
    wc_cols2[0].markdown(
        kpi_card_html(
            "Staff recruitment difficulty",
            f"{wf_overview['staff_rec_difficulty_pct']:.1f}%",
            colour=WCVA_BRAND["coral"],
        ),
        unsafe_allow_html=True,
    )
    wc_cols2[1].markdown(
        kpi_card_html(
            "Staff retention difficulty",
            f"{wf_overview['staff_ret_difficulty_pct']:.1f}%",
            colour=WCVA_BRAND["amber"],
        ),
        unsafe_allow_html=True,
    )
    wc_cols2[2].markdown(
        kpi_card_html(
            "Volunteer recruitment difficulty",
            f"{wf_overview['vol_rec_difficulty_pct']:.1f}%",
            colour=WCVA_BRAND["coral"],
        ),
        unsafe_allow_html=True,
    )

    # Distribution of paid staff numbers (among organisations with paid staff)
    staff_with_paid = df[df["paidworkforce"] == "Yes"]["peopleemploy"].dropna()
    if not staff_with_paid.empty:
        st.divider()
        st.subheader("Number of paid staff employed (organisations with paid staff)")
        # Simple banding scheme, aligned with the idea of small / medium / larger workforces.
        # Bin edges must be one longer than labels; we start bands at 1 because zero employees
        # are excluded by the paidworkforce == "Yes" filter and the dropna() above.
        bins = [1, 6, 21, 51, 251, float("inf")]
        labels = ["1–5", "6–20", "21–50", "51–250", "251+"]
        band_series = pd.cut(staff_with_paid, bins=bins, labels=labels, right=False)
        band_counts = band_series.value_counts().reindex(labels).fillna(0).astype(int)
        staff_base = int(band_counts.sum())
        bands_df = (
            pd.DataFrame(
                {
                    "Band": band_counts.index,
                    "Count": band_counts.values,
                }
            )
            .query("Count > 0")
            .reset_index(drop=True)
        )
        if not bands_df.empty:
            bands_df["pct"] = (bands_df["Count"] / max(staff_base, 1) * 100).round(1)
            fig_staff = horizontal_bar_ranked(
                bands_df,
                "Band",
                "Count",
                "Distribution of paid staff numbers (only organisations with paid staff)",
                staff_base,
                mode=palette_mode,
            )
            show_chart(
                fig_staff, "overview_staff_bands", bands_df[["Band", "Count", "pct"]]
            )

    # Cross-wave headline trend (Wave 1 vs Wave 2)
    with st.expander("Wave-to-wave headline trend (all organisations)"):
        registry = get_wave_registry(df)
        from src.wave_context import build_trend_long, build_trend_pivot

        trend_df = build_trend_long(registry)
        if trend_df.empty:
            st.info(
                "No cross-wave metrics are available yet. Add more waves or metrics to TREND_METRICS."
            )
        else:
            wide = build_trend_pivot(trend_df)
            st.dataframe(
                wide,
                hide_index=True,
                width="stretch",
            )
            st.caption(
                "Cross-wave comparison using the validated WaveContext schema. "
                "Columns show key headline indicators; additional metrics can be added "
                "via TREND_METRICS without changing this view."
            )

    col1, col2 = st.columns(2)
    alt_config = AltTextConfig(
        value_col="value", count_col="count", pct_col="pct", sample_size=n
    )

    with col1:
        st.subheader("Organisation Size")
        sizes = prof["org_size"]
        fig = donut_chart(
            list(sizes.keys()),
            list(sizes.values()),
            "Organisation size distribution",
            n,
            mode=palette_mode,
        )
        show_chart(
            fig, "overview_size", pd.DataFrame(sizes.items(), columns=["Size", "Count"])
        )

    with col2:
        st.subheader("Legal Form")
        lf = prof["legalform"]
        fig = donut_chart(
            list(lf.keys()),
            list(lf.values()),
            "Legal form distribution",
            n,
            mode=palette_mode,
        )
        show_chart(
            fig,
            "overview_legalform",
            pd.DataFrame(lf.items(), columns=["Form", "Count"]),
        )

    st.divider()
    st.subheader("Main activities of participating organisations")
    main_activities = prof["mainactivity"]
    if main_activities:
        ma_df = (
            pd.DataFrame(main_activities.items(), columns=["Activity", "Count"])
            .sort_values("Count", ascending=False)
            .reset_index(drop=True)
        )
        ma_df["pct"] = (ma_df["Count"] / max(n, 1) * 100).round(1)
        fig = horizontal_bar_ranked(
            ma_df,
            "Activity",
            "Count",
            "Main activities of participating organisations",
            n,
            mode=palette_mode,
        )
        show_chart(fig, "overview_mainactivity", ma_df[["Activity", "Count", "pct"]])
    else:
        st.caption("No main activity data available for this filtered view.")

    st.divider()
    st.subheader("Geographic Distribution of Respondents")
    col_la, col_region = st.columns([2, 1])
    with col_la:
        la_ctx = pd.DataFrame(prof["la_context"])
        la_ctx = la_ctx.sort_values("sample_count", ascending=False).reset_index(
            drop=True
        )
        total_sample = max(n, 1)
        total_pop = max(la_ctx["population_2024"].sum(), 1)
        la_ctx["sample_share_pct"] = la_ctx["sample_count"] / total_sample * 100.0
        la_ctx["pop_share_pct"] = la_ctx["population_2024"] / total_pop * 100.0
        la_ctx["representation_index"] = (
            la_ctx["sample_share_pct"] / la_ctx["pop_share_pct"]
        ).round(2)

        # It looks like the df `la_ctx` already has the `est_vcse_orgs` column
        # No need to merge again!
        # la_ctx = la_ctx.merge(
        #         prof["est_vcse_orgs"],
        #         on="local_authority",
        #         how="left",
        #         validate="one_to_one"
        #     )

        fig = horizontal_bar_ranked(
            la_ctx.rename(
                columns={
                    "local_authority": "Local Authority",
                    "sample_count": "Sample count",
                }
            ),
            "Local Authority",
            "Sample count",
            "Sample by local authority (raw counts)",
            n,
            mode=palette_mode,
            pct_col=None,
            height=550,
        )
        show_chart(
            fig,
            "overview_la",
            la_ctx[
                [
                    "local_authority",
                    "region",
                    "population_2024",
                    "sample_count",
                    "est_vcse_orgs",
                    "representation_index",
                ]
            ],
        )

        # Optional deeper dive: representation index by region
        with st.expander(
            "View over/under-representation by Local Authority (sample vs population)"
        ):
            rep_df = la_ctx.sort_values("representation_index", ascending=False).copy()
            rep_vis = rep_df.rename(
                columns={
                    "local_authority": "Local Authority",
                    "region": "Region",
                    "representation_index": "Representation index",
                }
            )
            fig_rep = horizontal_bar_ranked(
                rep_vis,
                "Local Authority",
                "Representation index",
                "Representation index by Local Authority (1.0 = proportional to population)",
                n,
                mode=palette_mode,
                pct_col=None,
                height=420,
            )
            show_chart(fig_rep, "overview_local_authority_repindex", rep_df)

    with col_region:
        ctx = pd.DataFrame(prof["la_context"])
        region_summary = ctx.groupby("region", as_index=False).agg(
            population_2024=("population_2024", "sum"),
            sample_count=("sample_count", "sum"),
        )
        total_sample = max(n, 1)
        total_pop = max(region_summary["population_2024"].sum(), 1)
        region_summary["sample_share_pct"] = (
            region_summary["sample_count"] / total_sample * 100.0
        )
        region_summary["pop_share_pct"] = (
            region_summary["population_2024"] / total_pop * 100.0
        )
        region_summary["representation_index"] = (
            region_summary["sample_share_pct"] / region_summary["pop_share_pct"]
        ).round(2)

        fig = donut_chart(
            list(region_summary["region"]),
            list(region_summary["sample_share_pct"].round(1)),
            "Sample share by region (%)",
            n,
            mode=palette_mode,
        )
        show_chart(fig, "overview_region", region_summary)

        # Optional deeper dive: representation index by region
        with st.expander(
            "View over/under-representation by region (sample vs population)"
        ):
            rep_df = region_summary.sort_values(
                "representation_index", ascending=False
            ).copy()
            rep_vis = rep_df.rename(
                columns={
                    "region": "Region",
                    "representation_index": "Representation index",
                }
            )
            fig_rep = horizontal_bar_ranked(
                rep_vis,
                "Region",
                "Representation index",
                "Representation index by region (1.0 = proportional to population)",
                n,
                mode=palette_mode,
                pct_col=None,
                height=420,
            )
            show_chart(fig_rep, "overview_region_repindex", rep_df)

    st.caption(
        "Note: Sample shares are compared against 2024 mid-year population estimates. "
        "Representation index of 1.0 indicates proportional-to-population sampling; values above 1.0 indicate over-representation."
    )

    st.divider()
    st.subheader("Recent Experience (Last 3 Months)")
    col3, col4 = st.columns(2)
    with col3:
        grouper, group_order = resolve_grouping(DEMAND_ORDER)
        fig = stacked_bar_ordinal(
            dem["demand"],
            "Demand for services has mostly increased",
            n,
            mode=palette_mode,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "overview_demand", dem["demand"])

    with col4:
        grouper, group_order = resolve_grouping(FINANCIAL_ORDER)
        fig = stacked_bar_ordinal(
            dem["financial"],
            "Financial position (last 3 mth): mostly unchanged, but a third report deterioration",
            n,
            mode=palette_mode,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "overview_financial", dem["financial"])

    # Narrative summary of the demand–finance “scissor effect”
    st.caption(demand_finance_scissor_phrase(dem))

    col5, col6 = st.columns(2)
    with col5:
        grouper, group_order = resolve_grouping(OPERATING_ORDER)
        fig = stacked_bar_ordinal(
            dem["operating"],
            "Most organisations expect to survive; but uncertainty exists",
            n,
            mode=palette_mode,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "overview_operating", dem["operating"])
    with col6:
        grouper, group_order = resolve_grouping(DEMAND_ORDER)
        fig = stacked_bar_ordinal(
            dem.get("workforce_change", dem["demand"]),
            "Workforce changes largely mirror demand trends",
            n,
            mode=palette_mode,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(
            fig, "overview_workforce", dem.get("workforce_change", dem["demand"])
        )

    st.divider()
    st.subheader("Looking Ahead (Next 3 Months)")
    col7, col8 = st.columns(2)
    with col7:
        grouper, group_order = resolve_grouping(EXPECT_DEMAND_ORDER)
        fig = stacked_bar_ordinal(
            dem["expect_demand"],
            "Organisations expect demand to keep rising",
            n,
            mode=palette_mode,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "overview_expect_demand", dem["expect_demand"])
    with col8:
        grouper, group_order = resolve_grouping(EXPECT_FINANCIAL_ORDER)
        fig = stacked_bar_ordinal(
            dem["expect_financial"],
            "Financial outlook: little optimism for improvement",
            n,
            mode=palette_mode,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "overview_expect_financial", dem["expect_financial"])

    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li>The KPI tiles at the top of this page and the stacked bar charts labelled "
        "<strong>Demand for services has mostly increased</strong> (top left, based on `demand_direction`) "
        "and <strong>Financial position (last 3 mth): mostly unchanged, but a third report deterioration</strong> (top right, based on "
        "`financial_direction`) provide the evidence for the Executive Summary narrative on the "
        "demand–capacity ‘scissor effect’.</li>"
        "<li>The expectations charts <strong>Organisations expect demand to keep rising</strong> "
        "(`expectdemand`) and <strong>Financial outlook: little optimism for improvement</strong> "
        "(`expectfinancial`) show the forward-looking components of that same story, supporting references "
        "to the outlook not improving in the next three months.</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )
