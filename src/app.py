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
    YES_NO_ORDER, SEVERITY_COLOURS, AltTextConfig, resolve_grouping,
    CHART_FONT_SIZE, CHART_TITLE_SIZE,
)
from src.wave_context import (
    WAVE1_CONTEXT,
    WaveRegistry,
    build_wave_registry_from_current_data,
    trend_series,
    TREND_METRICS,
    compare_demand_increase,
    compare_financial_deterioration,
)
from src.eda import (
    profile_summary, demand_and_outlook, volunteer_recruitment_analysis,
    volunteer_retention_analysis, workforce_operations, volunteer_demographics,
    volunteering_types, executive_highlights, cross_segment_analysis,
    finance_recruitment_cross,
)
from src.charts import (
    horizontal_bar_ranked, stacked_bar_ordinal, donut_chart,
    grouped_bar, heatmap_matrix, kpi_card_html,
)
from src.narratives import demand_finance_scissor_phrase, recruitment_vs_retention_phrase
import plotly.express as px
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


@st.cache_data
def get_wave_registry() -> WaveRegistry:
    """Shared cross-wave registry for trend analysis and narratives."""
    return build_wave_registry_from_current_data()

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
    "Trends & Waves",
    "Volunteer Recruitment",
    "Volunteer Retention",
    "Workforce & Operations",
    "Concerns & Risks",
    "Demographics & Types",
    "Earned Settlement",
    "Data Notes",
]

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Executive Summary"

page = st.sidebar.radio(
    "Navigate",
    pages,
    index=pages.index(st.session_state["current_page"]),
    label_visibility="collapsed",
)
st.session_state["current_page"] = page

prof = profile_summary(df)

# =========================================================================
# PAGE 1: At-a-Glance Infographic
# =========================================================================
if page == "At-a-Glance":
    st.title("State of Volunteering in Wales — At a Glance")
    st.caption("Baromedr Cymru — Wave 2 (organisational survey)")

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

    st.info(
        "These infographic headline percentages are drawn directly from the same aggregates used "
        "elsewhere in the dashboard: demand and finance from **Demand & Outlook**, and volunteer "
        "shortage and difficulty from the **Volunteer Recruitment** and **Volunteer Retention** analyses."
    )

    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li>The infographic cards are driven by the same columns used elsewhere in the dashboard: "
        "`demand_direction` and `financial_direction` feed the demand and finance metrics, while "
        "`volobjectives`, `vol_rec` and `vol_ret` feed the volunteer shortage and difficulty metrics. "
        "These are the same inputs that underpin Executive Summary highlights #2 (rising demand vs squeezed "
        "finances) and #3 (too few volunteers and recruitment difficulty).</li>"
        "<li>Any changes you see when applying filters here are reflected in how those stories would "
        "read for that segment of the sector.</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )

    with st.expander("View metrics as table"):
        metrics_rows = [
            {"Metric": "Organisations in view", "Value": str(n)},
            {"Metric": "Demand increased", "Value": f"{dem['demand_pct_increased']}%"},
            {"Metric": "Finances deteriorated", "Value": f"{dem['financial_pct_deteriorated']}%"},
            {"Metric": "Too few volunteers for need", "Value": f"{rec['pct_too_few']}%"},
            {"Metric": "Recruitment difficult", "Value": f"{rec['pct_difficulty']}%"},
            {"Metric": "Retention difficult", "Value": f"{ret['pct_difficulty']}%"},
        ]
        metrics_df = pd.DataFrame(metrics_rows, dtype="string")
        st.dataframe(metrics_df, hide_index=True, width="stretch")

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

    st.divider()
    st.subheader("Key questions for deeper analysis")
    st.markdown(
        "- How different are these pressures for smaller vs larger organisations, or by main activity?\n"
        "- Among organisations whose finances have deteriorated, is recruitment difficulty higher than for those with stable finances?\n"
        "- Where are volunteer shortages most acute, and which parts of the sector appear to be coping better?"
    )

    st.divider()
    st.subheader("Explore findings")
    nav_cols = st.columns(4)
    if nav_cols[0].button("Volunteer recruitment", use_container_width=True):
        st.session_state["current_page"] = "Volunteer Recruitment"
        st.rerun()
    if nav_cols[1].button("Volunteer retention", use_container_width=True):
        st.session_state["current_page"] = "Volunteer Retention"
        st.rerun()
    if nav_cols[2].button("Workforce & operations", use_container_width=True):
        st.session_state["current_page"] = "Workforce & Operations"
        st.rerun()
    if nav_cols[3].button("Policy & outlook", use_container_width=True):
        st.session_state["current_page"] = "Earned Settlement"
        st.rerun()


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

    st.info(
        "The overview KPI tiles for demand, finances and likelihood of operating are calculated from "
        "the **Demand & Outlook** aggregates shown further down this page; they share the same base and "
        "filters as the stacked bar charts for recent experience and expectations."
    )

    # Cross-wave headline trend (Wave 1 vs Wave 2)
    with st.expander("Wave-to-wave headline trend (all organisations)"):
        registry = get_wave_registry()
        from src.wave_context import build_trend_long, build_trend_pivot

        trend_df = build_trend_long(registry)
        if trend_df.empty:
            st.info("No cross-wave metrics are available yet. Add more waves or metrics to TREND_METRICS.")
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
        fig = stacked_bar_ordinal(dem["financial"], "Finances mostly unchanged, but a third report deterioration", n,
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

    st.subheader("How This Links to the Executive Summary")
    st.markdown(
        "<div style='border-left:4px solid {colour};padding:12px 16px;margin:8px 0;"
        "background:#F7F8FA;border-radius:4px'>"
        "<ul style='margin-top:4px;padding-left:18px;color:#333;font-size:0.9rem;'>"
        "<li>The KPI tiles at the top of this page and the stacked bar charts labelled "
        "<strong>Demand for services has mostly increased</strong> (top left, based on `demand_direction`) "
        "and <strong>Finances mostly unchanged, but a third report deterioration</strong> (top right, based on "
        "`financial_direction`) provide the evidence for the Executive Summary narrative on the "
        "demand–capacity ‘scissor effect’.</li>"
        "<li>The expectations charts <strong>Organisations expect demand to keep rising</strong> "
        "(`expectdemand`) and <strong>Financial outlook: little optimism for improvement</strong> "
        "(`expectfinancial`) show the forward-looking components of that same story, supporting references "
        "to the outlook not improving in the next three months.</li>"
        "</ul></div>".format(colour=WCVA_BRAND["blue"]),
        unsafe_allow_html=True,
    )


# =========================================================================
# PAGE 3: Volunteer Recruitment
# =========================================================================
elif page == "Volunteer Recruitment":
    st.title("Volunteer Recruitment")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    rec = volunteer_recruitment_analysis(df)
    # Cross-wave context for recruitment difficulty
    registry = get_wave_registry()
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
            mode=palette_mode,
            alt_config=alt_config_obj,
            grouper=grouper,
            group_order=group_order,
        )
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


# =========================================================================
# PAGE 4: Volunteer Retention
# =========================================================================
elif page == "Volunteer Retention":
    st.title("Volunteer Retention")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    ret = volunteer_retention_analysis(df)
    registry = get_wave_registry()
    vol_ret_trend = trend_series(
        registry,
        "workforce.headline.face_volunteer_retention_difficulties_pct",
    )

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
            mode=palette_mode,
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


# =========================================================================
# PAGE 5: Trends & Waves
# =========================================================================
elif page == "Trends & Waves":
    st.title("Trends Across Waves")
    st.caption("Compare headline indicators across survey waves using the validated WaveContext model.")

    registry = get_wave_registry()
    from src.wave_context import build_trend_long, build_trend_pivot, summarise_trend_changes

    trend_df = build_trend_long(registry)

    if trend_df.empty:
        st.info("No cross-wave metrics are available yet. Add more waves or metrics to TREND_METRICS.")
        st.stop()
    # Narrative summary for key metrics using earliest vs latest change
    key_metric_ids = ["demand_increase", "finance_deteriorated_costs", "too_few_volunteers", "has_reserves", "using_reserves"]
    summaries = summarise_trend_changes(trend_df, key_metric_ids)
    if summaries:
        lines = []
        for mid in key_metric_ids:
            summary = summaries.get(mid)
            if not summary:
                continue
            direction = "increased" if summary["change_pct_points"] > 0 else "decreased" if summary["change_pct_points"] < 0 else "was unchanged"
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
    st.dataframe(wide, hide_index=True, width="stretch")

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

                fig = px.line(
                    mdf,
                    x="wave_number",
                    y="value",
                    markers=True,
                    text="value",
                    labels={"wave_number": "Wave", "value": "Percent"},
                    title=metric_label,
                )
                fig.update_traces(textposition="top center")
                fig.update_xaxes(
                    tickvals=mdf["wave_number"],
                    ticktext=mdf["wave_label"],
                )

                # Build rich alt-text with wave counts and number of waves
                unique_waves = (
                    mdf[["wave_label", "wave_n"]]
                    .drop_duplicates()
                    .sort_values("wave_label")
                )
                wave_summaries = ", ".join(
                    f"{row.wave_label} (n={row.wave_n})"
                    for row in unique_waves.itertuples(index=False)
                )
                n_waves = unique_waves.shape[0]
                fig._alt_text = (
                    f"Trend line for {metric_label} across {n_waves} waves. "
                    f"Waves and respondent counts: {wave_summaries}."
                )

                show_chart(
                    fig,
                    key=f"trend_{section_name}_{metric_label}",
                    data_df=mdf[["wave_label", "wave_number", "wave_n", "value"]],
                )

    st.divider()
    st.subheader("Debug: EDA vs WaveContext (Wave 2)")

    with st.expander("Show comparison table for key metrics"):
        # Use the full (unfiltered) dataset for a clean Wave 2 comparison
        df_all = get_data()
        rec = volunteer_recruitment_analysis(df_all)
        wf = workforce_operations(df_all)

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


# =========================================================================
# PAGE 6: Workforce & Operations
# =========================================================================
elif page == "Workforce & Operations":
    st.title("Workforce & Operations")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    wf = workforce_operations(df)
    registry = get_wave_registry()
    staff_rec_trend = trend_series(
        registry,
        "workforce.headline.face_staff_recruitment_difficulties_pct",
    )

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


# =========================================================================
# PAGE 7: Concerns & Risks
# =========================================================================
elif page == "Concerns & Risks":
    st.title("Organisational Concerns & Risks")

    if suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    wf = workforce_operations(df)

    st.markdown(
        "This page shows the full distributions behind the executive summary statements "
        "about income, increasing demand, recruitment and retention concerns, and the "
        "operational impact of rising costs and shortages."
    )

    st.divider()
    st.subheader("Operational Concerns (current wave / filtered view)")
    fig = horizontal_bar_ranked(
        wf["concerns"],
        "label",
        "count",
        "Concerns organisations highlight as most pressing",
        n,
        mode=palette_mode,
    )
    show_chart(fig, "concerns_full", wf["concerns"][["label", "count", "pct"]])

    st.info(
        "The executive summary headline **“Income is the #1 concern”** and references to "
        "**increasing demand as the second most common concern** are derived directly from "
        "the ordering and percentages in the chart and table above."
    )

    st.divider()
    st.subheader("Concerns as Top Issues Across Waves")
    registry = get_wave_registry()
    from src.wave_context import build_trend_long, build_trend_pivot, summarise_trend_changes

    trend_df = build_trend_long(registry)
    concern_ids = ["income_top_concern", "demand_top_concern", "inflation_top_concern"]
    concerns_trend = trend_df[trend_df["metric_id"].isin(concern_ids)].copy()

    if concerns_trend.empty:
        st.info("No cross-wave concerns metrics are available yet. Add them to TREND_METRICS to enable this view.")
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
                    else "decreased"
                    if summary["change_pct_points"] < 0
                    else "was unchanged"
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
            fig_line = px.line(
                mdf,
                x="wave_number",
                y="value",
                markers=True,
                text="value",
                labels={"wave_number": "Wave", "value": "Percent"},
                title=metric_label,
            )
            fig_line.update_traces(textposition="top center")
            fig_line.update_xaxes(
                tickvals=mdf["wave_number"],
                ticktext=mdf["wave_label"],
            )
            unique_waves = (
                mdf[["wave_label", "wave_n"]]
                .drop_duplicates()
                .sort_values("wave_label")
            )
            wave_summaries = ", ".join(
                f"{row.wave_label} (n={row.wave_n})"
                for row in unique_waves.itertuples(index=False)
            )
            n_waves = unique_waves.shape[0]
            fig_line._alt_text = (
                f"Trend line for {metric_label} as a top concern across {n_waves} waves. "
                f"Waves and respondent counts: {wave_summaries}."
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
        mode=palette_mode,
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
        mode=palette_mode,
    )
    show_chart(fig, "concerns_shortage_affect", wf["shortage_affect"][["label", "count", "pct"]])

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


# =========================================================================
# PAGE 8: Demographics & Types
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


# =========================================================================
# PAGE 9: Earned Settlement
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
    registry = get_wave_registry()

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

    st.info(
        "All earned settlement statements on this page and in the executive summary are backed by the "
        "`earnedsettlement` Likert distribution and the `settlement_capacity` counts shown in the charts "
        "above, via the **Volunteering Types & Earned Settlement analysis** (`volunteering_types`)."
    )


# =========================================================================
# PAGE 10: Executive Summary
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
        "depend on the age ranges and definitions used in those population surveys; and it is important to know whether those surveys "
        "have excluded under‑15s or blurred boundaries with unpaid caring. In the longer term, "
        "triangulating these organisational findings with surveys of individual volunteers "
        "and non‑volunteers would give a fuller picture of volunteering in Wales. "
        "It is not all about headlines; distributions by organisation type and smaller response categories are also informative."
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

    cross = finance_recruitment_cross(df)
    if cross:
        st.info(
            f"**Finance–recruitment link**: Among organisations reporting deteriorating finances, "
            f"{cross['pct_rec_difficulty_if_finance_deteriorated']}% find recruitment difficult, compared with "
            f"{cross['pct_rec_difficulty_if_finance_not_deteriorated']}% among those whose finances have not deteriorated."
        )

    st.divider()
    st.subheader("Wave context across waves")
    registry = get_wave_registry()
    for label in registry.list_waves():
        wave_ctx = registry.get(label)
        bullet_lines = "".join(f"<li>{line}</li>" for line in wave_ctx.executive_context_callouts())
        st.markdown(
            f"<div style='border-left:4px solid {WCVA_BRAND['blue']};"
            f"background:#F7F8FA;padding:12px 16px;margin:8px 0;border-radius:4px;'>"
            f"<strong>{wave_ctx.meta.wave_label}</strong> "
            f"<span style='color:#555'>(n={wave_ctx.meta.wave_response_count})</span>"
            f"<ul style='margin-top:6px;padding-left:18px;color:#333;font-size:0.9rem;'>"
            f"{bullet_lines}</ul></div>",
            unsafe_allow_html=True,
        )

    # Simple earliest vs latest comparison for key headline metrics
    first_wave, latest_wave = registry.first_and_latest()
    dem_change = compare_demand_increase(first_wave, latest_wave)
    fin_change = compare_financial_deterioration(first_wave, latest_wave)
    st.info(
        f"From {dem_change['old_wave']} to {dem_change['new_wave']}, the share reporting increased demand "
        f"changed from {dem_change['old_value']}% to {dem_change['new_value']}% "
        f"({dem_change['change_pct_points']} percentage points). "
        f"Over the same period, the share reporting finances deteriorated due to rising costs shifted from "
        f"{fin_change['old_value']}% to {fin_change['new_value']}% "
        f"({fin_change['change_pct_points']} percentage points)."
    )

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

    if "Main activity" in seg:
        st.subheader("Key Metrics by Main activity")
        act_data = seg["Main activity"]
        act_rows = [
            {
                "Main activity": name,
                "n": d["n"],
                "Demand increased %": d["pct_demand_increased"],
                "Finance deteriorated %": d["pct_finance_deteriorated"],
                "Vol. recruitment difficulty %": d["pct_vol_rec_difficulty"],
                "Too few volunteers %": d["pct_too_few_vols"],
            }
            for name, d in sorted(act_data.items(), key=lambda x: -x[1]["n"])[:10]
        ]
        if act_rows:
            st.dataframe(pd.DataFrame(act_rows), hide_index=True, width="stretch")
        st.caption("Top 10 activities by sample size. Smaller segments are also informative.")

    st.divider()
    st.subheader("Policy Recommendations")
    # Derive dynamic metrics for volunteer offers (expenses vs financial signposting)
    ret_offer = volunteer_retention_analysis(df)["vol_offer"]
    exp_row = ret_offer[ret_offer["label"] == "Covering expenses"]
    sign_row = ret_offer[ret_offer["label"] == "Financial advice signposting"]
    expenses_pct = exp_row["pct"].iloc[0] if not exp_row.empty else None
    signpost_pct = sign_row["pct"].iloc[0] if not sign_row.empty else None

    if expenses_pct is not None and signpost_pct is not None:
        funding_vol_sentence = (
            f"Expenses coverage is widespread ({expenses_pct}% of organisations), "
            f"but only {signpost_pct}% offer financial signposting."
        )
    elif signpost_pct is not None:
        funding_vol_sentence = f"Only {signpost_pct}% of organisations offer financial signposting."
    else:
        funding_vol_sentence = (
            "Expenses coverage is widespread but financial signposting remains relatively rare."
        )

    st.markdown(f"""
1. **Invest in recruitment infrastructure** — Organisations are trying but getting low response. Centralised campaigns via TSSW/CVCs could boost reach.
2. **Address the funding-volunteer gap** — {funding_vol_sentence} Signposting to cost-of-living support for volunteers is a retention lever.
3. **Build flexible volunteering models** — Retention barriers are largely external (life changes). Micro-volunteering, remote roles, and flexible commitments can accommodate these realities.
4. **Prepare for earned settlement** — Sentiment is positive but capacity is low. Early guidance and resource allocation will determine whether this becomes an opportunity or a burden.
5. **Monitor demand-capacity divergence** — Demand is rising, finances are flat or declining, and reserves are being depleted. Without intervention, service reductions will accelerate.
""")

    st.subheader("Future analysis opportunities")
    st.markdown("""
- **Segment by organisation type**: A deeper cut by main activity (e.g. environment vs health vs advice services)
  could show where pressures are most acute and where resilience is strongest.
- **Link finance and recruitment challenges**: Exploring how financial strain, staffing levels, and investment in
  volunteer coordination interact would help target support more precisely.
""")


# =========================================================================
# PAGE 11: Data Notes
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
