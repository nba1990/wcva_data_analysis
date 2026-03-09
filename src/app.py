"""
Baromedr Cymru Wave 2 — Interactive Analysis Dashboard

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from src.data_loader import load_dataset, data_quality_profile
from src.config import (
    DEMAND_ORDER, DIFFICULTY_ORDER, EARNED_SETTLEMENT_ORDER,
    EXPECT_DEMAND_ORDER, EXPECT_FINANCIAL_ORDER,
    FINANCIAL_ORDER, K_ANON_THRESHOLD, OPERATING_ORDER,
    VOL_OBJECTIVES_ORDER, VOL_TYPEUSE_ORDER, WCVA_BRAND, ORG_SIZE_ORDER,
    YES_NO_ORDER, WAVE1_CONTEXT, SEVERITY_COLOURS, AltTextConfig, resolve_grouping,
    CHART_FONT_SIZE, CHART_TITLE_SIZE,
)
from src.eda import (
    profile_summary, demand_and_outlook, volunteer_recruitment_analysis,
    volunteer_retention_analysis, workforce_operations, volunteer_demographics,
    volunteering_types, executive_highlights, cross_segment_analysis,
)
from src.charts import (
    horizontal_bar_ranked, stacked_bar_ordinal, donut_chart,
    grouped_bar, heatmap_matrix, kpi_card_html,
)
from src.narratives import demand_finance_scissor_phrase, recruitment_vs_retention_phrase
from src.infographic import render_at_a_glance_infographic

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
def get_data():
    return load_dataset()

df_full = get_data()  # Shape of dataset: (111, 162) (111 organisations, 162 variables) # noqa

# ---------------------------------------------------------------------------
# Sidebar: filters + accessibility toggle
# ---------------------------------------------------------------------------
st.sidebar.title("Baromedr Cymru")
st.sidebar.caption("Wave 2 Analysis Dashboard")
st.sidebar.divider()

accessible_mode = st.sidebar.checkbox("Colour-blind friendly mode", value=False)
palette_mode = "accessible" if accessible_mode else "brand"

text_size_mode = st.sidebar.radio(
    "Chart label size",
    ["Normal", "Larger"],
    index=0,
)
TEXT_SCALE = 1.0 if text_size_mode == "Normal" else 1.3

st.sidebar.divider()
st.sidebar.subheader("Filters")

size_options = ["All"] + ORG_SIZE_ORDER
selected_size = st.sidebar.selectbox("Organisation size", size_options)

scope_options = ["All"] + sorted(df_full["wales_scope"].dropna().unique().tolist())
selected_scope = st.sidebar.selectbox("Geographic scope", scope_options)

la_scope_options = ["All"] + sorted(df_full["location_la_primary"].dropna().unique().tolist())
selected_la_scope = st.sidebar.selectbox("Local primary authority scope", la_scope_options)

activity_options = ["All"] + sorted(df_full["mainactivity"].dropna().unique().tolist())
selected_activity = st.sidebar.selectbox("Main activity", activity_options)

df = df_full.copy()

# Apply filters (if selected, default is "All")
if selected_size != "All":
    df = df[df["org_size"] == selected_size]
if selected_scope != "All":
    df = df[df["wales_scope"] == selected_scope]
if selected_la_scope != "All":
    df = df[df["location_la_primary"] == selected_la_scope]
if selected_activity != "All":
    df = df[df["mainactivity"] == selected_activity]

n = len(df)
suppressed = n < K_ANON_THRESHOLD

if suppressed:
    st.sidebar.warning(
        f"⚠️ Only **{n}** organisations match these filters (below the privacy "
        f"threshold of {K_ANON_THRESHOLD}). Results are suppressed to protect respondent anonymity."
    )

st.sidebar.divider()
st.sidebar.caption(f"Showing **{n}** of {len(df_full)} organisations")

# ---------------------------------------------------------------------------
# Helper: chart display with download
# ---------------------------------------------------------------------------

def show_chart(fig, key: str, data_df: pd.DataFrame | None = None):
    """Display a Plotly chart with optional download buttons."""
    # Apply dynamic text scaling from sidebar control
    if TEXT_SCALE != 1.0:
        fig.update_layout(
            font=dict(size=CHART_FONT_SIZE * TEXT_SCALE),
            title_font_size=CHART_TITLE_SIZE * TEXT_SCALE,
            legend=dict(font=dict(size=CHART_FONT_SIZE * TEXT_SCALE)),
        )
        fig.update_xaxes(tickfont_size=CHART_FONT_SIZE * TEXT_SCALE)
        fig.update_yaxes(tickfont_size=CHART_FONT_SIZE * TEXT_SCALE)

    st.plotly_chart(fig, width="stretch", key=key)
    if hasattr(fig, "_alt_text"):
        st.caption(f"Accessibility: {fig._alt_text}")

    if data_df is not None:
        with st.expander("View/download data table"):
            # st.dataframe(data_df, use_container_width=True)
            # use_container_width=True is deprecated and is already removed in Streamlit since 2025-12-31
            st.dataframe(data_df, width="stretch")
            csv = data_df.to_csv(index=False)
            st.download_button("Download CSV", csv, f"{key}.csv", "text/csv", key=f"dl_{key}")


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
pages = [
    "Executive Summary",
    "At-a-Glance",
    "Overview",
    "Volunteer Recruitment",
    "Volunteer Retention",
    "Workforce & Operations",
    "Demographics & Types",
    "Earned Settlement",
    "Data Notes",
]

page = st.sidebar.radio("Navigate", pages, label_visibility="collapsed")

prof = profile_summary(df)

# =========================================================================
# PAGE 1: At-a-Glance Infographic
# =========================================================================
if page == "At-a-Glance":
    st.title("Baromedr Cymru — At a Glance")

    if suppressed:
        st.warning("Results suppressed due to small sample size. Adjust filters to see data.")
        st.stop()

    dem = demand_and_outlook(df)
    rec = volunteer_recruitment_analysis(df)
    ret = volunteer_retention_analysis(df)

    render_at_a_glance_infographic(n, dem, rec, ret)
    st.caption(
        "Poster-style summary of how rising demand, finances, and volunteer gaps "
        "interact in this filtered view of the survey."
    )

    with st.expander("View metrics as table"):
        metrics_rows = [
            {"Metric": "Organisations in view", "Value": n},
            {"Metric": "Demand increased", "Value": f"{dem['demand_pct_increased']}%"},
            {"Metric": "Finances deteriorated", "Value": f"{dem['financial_pct_deteriorated']}%"},
            {"Metric": "Too few volunteers for need", "Value": f"{rec['pct_too_few']}%"},
            {"Metric": "Recruitment difficult", "Value": f"{rec['pct_difficulty']}%"},
            {"Metric": "Retention difficult", "Value": f"{ret['pct_difficulty']}%"},
        ]
        st.dataframe(pd.DataFrame(metrics_rows), hide_index=True, width="stretch")

    st.divider()
    st.subheader("Demand–Capacity Story in One View")
    story_cols = st.columns(2)
    with story_cols[0]:
        st.markdown(f"- {demand_finance_scissor_phrase(dem)}")
        st.markdown("- " + recruitment_vs_retention_phrase(rec, ret))
    with story_cols[1]:
        st.markdown(
            "- Most organisations say they have **too few volunteers** for what they are trying to deliver."
        )
        st.markdown(
            "- Use the filters on the left to see how this picture changes by size, scope, LA, or activity."
        )


# =========================================================================
# PAGE 2: Overview
# =========================================================================
elif page == "Overview":
    st.title("Baromedr Cymru Wave 2 — Overview")

    if suppressed:
        st.warning("Results suppressed due to small sample size. Adjust filters to see data.")
        st.stop()

    dem = demand_and_outlook(df)

    cols = st.columns(4)
    cols[0].markdown(kpi_card_html("Organisations", str(n), colour=WCVA_BRAND["teal"]), unsafe_allow_html=True)
    cols[1].markdown(kpi_card_html("Demand increasing", f"{dem['demand_pct_increased']}%", colour=WCVA_BRAND["amber"]), unsafe_allow_html=True)
    cols[2].markdown(kpi_card_html("Finances deteriorated", f"{dem['financial_pct_deteriorated']}%", colour=WCVA_BRAND["coral"]), unsafe_allow_html=True)
    cols[3].markdown(kpi_card_html("Likely operating next yr", f"{dem['operating_pct_likely']}%", colour=WCVA_BRAND["teal"]), unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    alt_config = AltTextConfig(value_col="value", count_col="count", pct_col="pct", sample_size=n)
    
    with col1:
        st.subheader("Organisation Size")
        sizes = prof["org_size"]
        fig = donut_chart(list(sizes.keys()), list(sizes.values()), "Organisation size distribution", n, mode=palette_mode)
        show_chart(fig, "overview_size", pd.DataFrame(sizes.items(), columns=["Size", "Count"]))

    with col2:
        st.subheader("Legal Form")
        lf = prof["legalform"]
        fig = donut_chart(list(lf.keys()), list(lf.values()), "Legal form distribution", n, mode=palette_mode)
        show_chart(fig, "overview_legalform", pd.DataFrame(lf.items(), columns=["Form", "Count"]))

    st.divider()
    st.subheader("Geographic Distribution of Respondents")
    col_la, col_region = st.columns([2, 1])
    with col_la:
        la_ctx = pd.DataFrame(prof["la_context"])
        la_ctx = la_ctx.sort_values("sample_count", ascending=False).reset_index(drop=True)
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
            la_ctx.rename(columns={"local_authority": "Local Authority", "sample_count": "Sample count"}),
            "Local Authority",
            "Sample count",
            "Sample by local authority (raw counts)",
            n,
            mode=palette_mode,
            pct_col=None,
            height=550,
        )
        show_chart(fig, "overview_la", la_ctx[["local_authority", "region", "population_2024", "sample_count", "est_vcse_orgs", "representation_index"]])

        # Optional deeper dive: representation index by region
        with st.expander("View over/under-representation by Local Authority (sample vs population)"):
            rep_df = la_ctx.sort_values("representation_index", ascending=False).copy()
            rep_vis = rep_df.rename(
                columns={"local_authority": "Local Authority", "region": "Region", "representation_index": "Representation index"}
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
        region_summary = (
            ctx.groupby("region", as_index=False)
            .agg(
                population_2024=("population_2024", "sum"),
                sample_count=("sample_count", "sum"),
            )
        )
        total_sample = max(n, 1)
        total_pop = max(region_summary["population_2024"].sum(), 1)
        region_summary["sample_share_pct"] = region_summary["sample_count"] / total_sample * 100.0
        region_summary["pop_share_pct"] = region_summary["population_2024"] / total_pop * 100.0
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
        with st.expander("View over/under-representation by region (sample vs population)"):
            rep_df = region_summary.sort_values("representation_index", ascending=False).copy()
            rep_vis = rep_df.rename(
                columns={"region": "Region", "representation_index": "Representation index"}
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
        fig = stacked_bar_ordinal(dem["demand"], "Demand for services has mostly increased", n,
                                  mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "overview_demand", dem["demand"])

    with col4:
        grouper, group_order = resolve_grouping(FINANCIAL_ORDER)
        fig = stacked_bar_ordinal(dem["financial"], "Half report stable finances; a third are deteriorating", n,
                                  mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "overview_financial", dem["financial"])

    # Narrative summary of the demand–finance “scissor effect”
    st.caption(demand_finance_scissor_phrase(dem))

    col5, col6 = st.columns(2)
    with col5:
        grouper, group_order = resolve_grouping(OPERATING_ORDER)
        fig = stacked_bar_ordinal(dem["operating"], "Most organisations expect to survive; but uncertainty exists", n,
                                  mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "overview_operating", dem["operating"])
    with col6:
        grouper, group_order = resolve_grouping(DEMAND_ORDER)
        fig = stacked_bar_ordinal(dem.get("workforce_change", dem["demand"]),
                                  "Workforce changes largely mirror demand trends", n,
                                  mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "overview_workforce", dem.get("workforce_change", dem["demand"]))

    st.divider()
    st.subheader("Looking Ahead (Next 3 Months)")
    col7, col8 = st.columns(2)
    with col7:
        grouper, group_order = resolve_grouping(EXPECT_DEMAND_ORDER)
        fig = stacked_bar_ordinal(dem["expect_demand"], "Organisations expect demand to keep rising", n,
                                  mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "overview_expect_demand", dem["expect_demand"])
    with col8:
        grouper, group_order = resolve_grouping(EXPECT_FINANCIAL_ORDER)
        fig = stacked_bar_ordinal(dem["expect_financial"], "Financial outlook: little optimism for improvement", n,
                                  mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "overview_expect_financial", dem["expect_financial"])


# =========================================================================
# PAGE 2: Volunteer Recruitment
# =========================================================================
elif page == "Volunteer Recruitment":
    st.title("Volunteer Recruitment")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    rec = volunteer_recruitment_analysis(df)

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
    alt_config = AltTextConfig(value_col="value", count_col="count", pct_col="pct", sample_size=n)
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
        fig = stacked_bar_ordinal(rec["vol_rec_difficulty"], TITLE, diff_base, mode=palette_mode, alt_config=alt_config_diff,
                                  grouper=grouper, group_order=group_order)
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
        fig = stacked_bar_ordinal(rec["vol_objectives"], TITLE, n, mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "rec_objectives", rec["vol_objectives"])

    st.subheader("Top Recruitment Methods Used")
    fig = horizontal_bar_ranked(rec["rec_methods"], "label", "count", "Word of mouth dominates, but digital channels are close behind", n, mode=palette_mode)
    show_chart(fig, "rec_methods", rec["rec_methods"][["label", "count", "pct"]])

    st.subheader("Top Barriers to Recruitment")
    fig = horizontal_bar_ranked(rec["rec_barriers"], "label", "count", "The problem isn't lack of effort. It's low response and limited capacity", n, mode=palette_mode)
    show_chart(fig, "rec_barriers", rec["rec_barriers"][["label", "count", "pct"]])

    if "Large" in rec["rec_barriers_by_size"].columns and "Small" in rec["rec_barriers_by_size"].columns:
        st.subheader("Barriers by Organisation Size")
        seg_cols = [c for c in ORG_SIZE_ORDER if c in rec["rec_barriers_by_size"].columns]
        fig = grouped_bar(rec["rec_barriers_by_size"], "label", seg_cols, "How barriers differ by organisation size", n, mode=palette_mode)
        show_chart(fig, "rec_barriers_seg", rec["rec_barriers_by_size"])


# =========================================================================
# PAGE 3: Volunteer Retention
# =========================================================================
elif page == "Volunteer Retention":
    st.title("Volunteer Retention")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    ret = volunteer_retention_analysis(df)

    alt_config = AltTextConfig(value_col="value", count_col="count", pct_col="pct", sample_size=n)
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

    st.subheader("Retention Barriers")
    fig = horizontal_bar_ranked(ret["ret_barriers"], "label", "count", "Volunteers leave for life reasons; not dissatisfaction", n, mode=palette_mode)
    show_chart(fig, "ret_barriers", ret["ret_barriers"][["label", "count", "pct"]])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("What Organisations Offer Volunteers")
        fig = horizontal_bar_ranked(ret["vol_offer"], "label", "count", "Expenses coverage leads, but financial signposting is rare", n, mode=palette_mode)
        show_chart(fig, "ret_offer", ret["vol_offer"][["label", "count", "pct"]])

    with col2:
        st.subheader("Retention Difficulty")
        grouper, group_order = resolve_grouping(DIFFICULTY_ORDER)
        TITLE = "Retention is easier than recruitment; but challenges persist"
        fig = stacked_bar_ordinal(ret["vol_ret_difficulty"], TITLE, n, mode=palette_mode, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "ret_difficulty", ret["vol_ret_difficulty"])

    st.caption(
        f"{ret['pct_shortage']}% of organisations explicitly report a shortage retaining volunteers "
        "(shortage_vol_ret = 'Yes'), while {ret['pct_difficulty']}% find retention somewhat or "
        "extremely difficult on the Likert scale."
    )


# =========================================================================
# PAGE 4: Workforce & Operations
# =========================================================================
elif page == "Workforce & Operations":
    st.title("Workforce & Operations")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    wf = workforce_operations(df)

    cols = st.columns(4)
    cols[0].markdown(kpi_card_html("Finances deteriorated", f"{wf['finance_deteriorated_pct']}%", colour=WCVA_BRAND["coral"]), unsafe_allow_html=True)
    cols[1].markdown(kpi_card_html("Have reserves", f"{wf['reserves_yes_pct']}%", colour=WCVA_BRAND["teal"]), unsafe_allow_html=True)
    cols[2].markdown(kpi_card_html("Using reserves", f"{wf['using_reserves_pct']}%", delta="of those with reserves", colour=WCVA_BRAND["amber"]), unsafe_allow_html=True)
    cols[3].markdown(kpi_card_html("Median reserves", f"{wf['median_months_reserves']:.0f} months" if pd.notna(wf['median_months_reserves']) else "N/A", colour=WCVA_BRAND["blue"]), unsafe_allow_html=True)

    st.divider()

    st.subheader("Top 3 Concerns")
    fig = horizontal_bar_ranked(wf["concerns"], "label", "count", "Income dominates concerns, with demand and volunteer recruitment close behind", n, mode=palette_mode)
    show_chart(fig, "wf_concerns", wf["concerns"][["label", "count", "pct"]])

    st.subheader("Actions Taken Due to Rising Costs")
    fig = horizontal_bar_ranked(wf["actions"], "label", "count", "Price increases and unplanned reserves usage are the most common responses", n, mode=palette_mode)
    show_chart(fig, "wf_actions", wf["actions"][["label", "count", "pct"]])

    st.divider()
    st.subheader("Impact of Shortages")
    fig = horizontal_bar_ranked(wf["shortage_affect"], "label", "count",
                                "Unable to meet demand and paused operations are the most common consequences",
                                n, mode=palette_mode)
    show_chart(fig, "wf_shortage_affect", wf["shortage_affect"][["label", "count", "pct"]])

    st.divider()
    st.subheader("Staff Recruitment & Retention Difficulty")
    alt_config_wf = AltTextConfig(value_col="value", count_col="count", pct_col="pct", sample_size=wf["n_with_staff"])
    col_sr, col_sret = st.columns(2)
    with col_sr:
        grouper, group_order = resolve_grouping(YES_NO_ORDER)
        fig = stacked_bar_ordinal(wf["staff_rec_difficulty"],
                                  f"Staff recruitment difficulty (n={wf['n_with_staff']} with paid staff)",
                                  wf["n_with_staff"], mode=palette_mode, alt_config=alt_config_wf,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "wf_staff_rec", wf["staff_rec_difficulty"])
    with col_sret:
        fig = stacked_bar_ordinal(wf["staff_ret_difficulty"],
                                  f"Staff retention difficulty (n={wf['n_with_staff']} with paid staff)",
                                  wf["n_with_staff"], mode=palette_mode, alt_config=alt_config_wf,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "wf_staff_ret", wf["staff_ret_difficulty"])


# =========================================================================
# PAGE 5: Demographics & Types
# =========================================================================
elif page == "Demographics & Types":
    st.title("Volunteer Demographics & Volunteering Types")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    vd = volunteer_demographics(df)
    vt = volunteering_types(df)

    st.subheader("Volunteer Age/Group Presence (Last 12 Months)")
    alt_config = AltTextConfig(value_col="value", count_col="count", pct_col="pct", sample_size=n)
    fig = horizontal_bar_ranked(vd["dem_presence"], "label", "count", "26–64 age groups are the core volunteer base", n, mode=palette_mode, exclude_na=False)
    show_chart(fig, "dem_presence", vd["dem_presence"][["label", "count", "pct"]])

    if not vd["change_matrix"].empty:
        st.subheader("How Volunteer Numbers Changed by Group")
        change_cols = vd["change_order"]

        fig = heatmap_matrix(vd["change_matrix"], "group", change_cols, "Most groups stayed stable, with pockets of growth and decline", n, mode=palette_mode, height=500)

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
            mode=palette_mode,
            view="collapsed",  # "full" -> all columns visible, "collapsed" -> only three columns visible
        )

        show_chart(fig, "dem_change", vd["change_matrix"])

    st.divider()
    st.subheader("Change in Total Volunteer Time (Last 12 Months)")
    grouper, group_order = resolve_grouping(DEMAND_ORDER)
    fig = stacked_bar_ordinal(vd["vol_time"], "How has total volunteer time changed?", n,
                              mode=palette_mode, alt_config=alt_config,
                              grouper=grouper, group_order=group_order)
    show_chart(fig, "dem_vol_time", vd["vol_time"])

    st.divider()
    st.subheader("Types of Volunteering Used")
    for label, type_df in vt["type_data"].items():
        grouper, group_order = resolve_grouping(VOL_TYPEUSE_ORDER)
        fig = stacked_bar_ordinal(type_df, f"Types of Volunteering Used: {label}", n,
                                  mode=palette_mode, height=140, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, f"type_{label.replace(' ', '_')}", type_df)


# =========================================================================
# PAGE 6: Earned Settlement
# =========================================================================
elif page == "Earned Settlement":
    st.title("Earned Settlement Policy")
    st.markdown(
        "The Home Office's *Earned Settlement* proposal considers whether volunteering could "
        "count towards the time migrants need to qualify for permanent UK residency."
    )

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    vt = volunteering_types(df)

    col1, col2 = st.columns(2)
    alt_config = AltTextConfig(value_col="value", count_col="count", pct_col="pct", sample_size=n)
    with col1:
        st.subheader("Sentiment")
        grouper, group_order = resolve_grouping(EARNED_SETTLEMENT_ORDER)
        TITLE = "More agree than disagree. But a large neutral/unsure group still exists"
        fig = stacked_bar_ordinal(vt["earned_settlement"], TITLE, n, mode=palette_mode, height=220, alt_config=alt_config,
                                  grouper=grouper, group_order=group_order)
        show_chart(fig, "es_sentiment", vt["earned_settlement"])

    with col2:
        st.subheader("Organisational Capacity")
        cap = vt["settlement_capacity"]
        cap_df = pd.DataFrame(cap.items(), columns=["Capacity", "Count"]).sort_values("Count", ascending=False)
        fig = horizontal_bar_ranked(cap_df, "Capacity", "Count", "Most would need additional resources or guidance to support this", n, mode=palette_mode, pct_col=None, height=350)
        show_chart(fig, "es_capacity", cap_df)

    st.info(
        "**Policy implication**: Sentiment is cautiously positive, but implementation would "
        "require significant support both in resources and clear guidance. Without it, the "
        "policy risks becoming an unfunded mandate."
    )


# =========================================================================
# PAGE 7: Executive Summary
# =========================================================================
elif page == "Executive Summary":
    st.title("Executive Summary — Key Findings")
    st.caption("Baromedr Cymru Wave 2 | Volunteering in the Welsh Voluntary Sector")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    st.markdown(
        "This summary is based on an organisational survey. Headline claims about how many "
        "people in Wales volunteer (for example, that around one-third of adults volunteer) "
        "depend on the age ranges and definitions used in those population surveys, and may "
        "exclude under‑15s or blur boundaries with unpaid caring. In the longer term, "
        "triangulating these organisational findings with surveys of individual volunteers "
        "and non‑volunteers would give a fuller picture of volunteering in Wales."
    )

    highlights = executive_highlights(df)

    for h in highlights:
        colour = SEVERITY_COLOURS.get(h["type"], WCVA_BRAND["navy"])
        st.markdown(
            f"<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
            f"background:#F7F8FA;border-radius:4px'>"
            f"<strong style='color:{colour}'>#{h['rank']}: {h['title']}</strong><br>"
            f"<span style='color:#555'>{h['detail']}</span></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("Wave 1 Context")
    for key, desc in WAVE1_CONTEXT.items():
        if key.endswith("_desc"):
            st.markdown(f"- {desc}")

    st.divider()
    st.subheader("Key Metrics by Organisation Size")
    seg = cross_segment_analysis(df)
    if "Organisation Size" in seg:
        seg_data = seg["Organisation Size"]
        seg_rows = []
        for size in ORG_SIZE_ORDER:
            if size in seg_data:
                d = seg_data[size]
                seg_rows.append({
                    "Size": f"{size} (n={d['n']})",
                    "Demand increased %": d["pct_demand_increased"],
                    "Finance deteriorated %": d["pct_finance_deteriorated"],
                    "Vol. recruitment difficulty %": d["pct_vol_rec_difficulty"],
                    "Vol. retention difficulty %": d["pct_vol_ret_difficulty"],
                    "Too few volunteers %": d["pct_too_few_vols"],
                })
        if seg_rows:
            st.dataframe(pd.DataFrame(seg_rows), hide_index=True, width="stretch")

    st.divider()
    st.subheader("Policy Recommendations")
    st.markdown("""
1. **Invest in recruitment infrastructure** — Organisations are trying but getting low response. Centralised campaigns via TSSW/CVCs could boost reach.
2. **Address the funding-volunteer gap** — Expenses coverage is widespread but only 17% offer financial signposting. Cost-of-living support for volunteers is a retention lever.
3. **Build flexible volunteering models** — Retention barriers are largely external (life changes). Micro-volunteering, remote roles, and flexible commitments can accommodate these realities.
4. **Prepare for earned settlement** — Sentiment is positive but capacity is low. Early guidance and resource allocation will determine whether this becomes an opportunity or a burden.
5. **Monitor demand-capacity divergence** — Demand is rising, finances are flat or declining, and reserves are being depleted. Without intervention, service reductions will accelerate.
""")


# =========================================================================
# PAGE 8: Data Notes
# =========================================================================
elif page == "Data Notes":
    st.title("Data Notes & Methodology")

    dq = data_quality_profile(df_full)

    st.subheader("Dataset Overview")
    cols = st.columns(4)
    cols[0].metric("Total respondents", dq["n_rows"])
    cols[1].metric("Variables", dq["n_cols"])
    cols[2].metric("Missing org size", dq["org_size_missing"])
    cols[3].metric("Missing local authority", dq["la_missing"])

    st.divider()

    st.subheader("Response Completeness by Question Block")
    block_df = pd.DataFrame(
        dq["block_completeness"].items(), columns=["Question Block", "Completeness (%)"]
    ).sort_values("Completeness (%)", ascending=False)
    # st.dataframe(block_df, use_container_width=True, hide_index=True)
    # use_container_width=True is deprecated and is already removed in Streamlit since 2025-12-31
    st.dataframe(block_df, width="stretch", hide_index=True)

    st.divider()

    st.subheader("Methodology Notes")
    st.markdown("""
- **Survey**: Baromedr Cymru Wave 2, conducted in collaboration with NTU VCSE Observatory
- **Likert Scale**: A psychometric, often 5 or 7-point, survey rating system used to measure attitudes, opinions, and behaviors by gauging the level of agreement, frequency, or satisfaction. **Refer:** [Likert Scale](https://en.wikipedia.org/wiki/Likert_scale) for more information.
- **Period**: January–February 2026
- **Sample**: 111 Welsh voluntary sector organisations (self-selected; not a random sample)
- **Format**: Online survey via Qualtrics; 10–15 minute completion time
- **Multi-select questions**: Presented in wide format (one column per option; non-null = selected)
- **Privacy**: All data anonymised prior to analysis. Results suppressed when filtered sample < 5 organisations (k-anonymity)
""")

    st.subheader("Definitions of volunteering")
    st.markdown("""
- **Volunteering vs unpaid caring**: This analysis follows the Baromedr definition of volunteering
  and does not treat unpaid caring roles (for family members, for example) as volunteering.
- **Formal and informal activity**: Many real-world examples (e.g. community clean-ups, emergency response,
  neighbourhood action) can sit on the boundary between formal and informal volunteering. Where possible,
  Baromedr questions focus on activity that organisations can reasonably observe and report.
- **Age ranges**: Headline figures from other sources about the share of people who volunteer often use specific
  age bands (for example 16–74 or 15–85). Under‑15s and very elderly volunteers may therefore be under-represented
  in population estimates, even if organisations rely on them in practice.
""")

    st.subheader("Caveats")
    st.markdown("""
- **Self-selection bias**: Respondents chose to participate; findings may not represent all Welsh voluntary sector organisations
- **Cardiff over-representation (raw counts)**: 23% of respondents are Cardiff-based; interpret geographic patterns with caution
- **Powys over-representation (proportional to population)**: 2.34 representation index - respondents are Powys-based; interpret geographic patterns with caution. **NOTE:** Representation index of 1.0 indicates proportional-to-population sampling; values above 1.0 indicate over-representation.
- **Small sub-groups**: Some local authority and activity type segments have very few respondents. Avoid over-interpreting these segments
- **Wave 2 only**: Cross-wave trend analysis requires Wave 1 data (not included in this dataset)
- **Ordinal data**: Likert-scale responses are ordinal, not interval. Median is more appropriate than mean
""")

    st.subheader("Estimated Number of VCSE Organisations in Wales")
    st.markdown("""
- For the `est_vcse_orgs` column, it appeas to not be so simple to fully validate those numbers as official local-authority counts counts from an authoritative Wales-wide source.
- There appears to be some good sector-level sources, but not a clean official table matching this column definition.
- The reason is that Welsh sector sources use different universes:
  - WCVA says Wales has **32,000+** third sector organisations
  - While NCVO reports **7,009** charities in Wales in its 2023 Almanac
  - Equal to about **2.3 organisations** per 1,000 people.
- The pre-populated helper CSV sums up to **14,980** organisations, which is about **4.7** per **1,000** people using the total population.
- That sits neatly between the “registered charities only” count and the broader “all third sector organisations” count.
- Therefore, `est_vcse_orgs` is only considered plausible as a modelled estimate, but not validated as an official observed count.
""")
