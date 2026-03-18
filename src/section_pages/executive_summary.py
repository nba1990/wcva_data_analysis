# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import ORG_SIZE_ORDER, SEVERITY_COLOURS, WCVA_BRAND
from src.eda import (
    cross_segment_analysis,
    demand_and_outlook,
    executive_highlights,
    finance_recruitment_cross,
    volunteer_recruitment_analysis,
    volunteer_retention_analysis,
    workforce_operations,
)
from src.page_context import PageContext
from src.wave_context import build_wave_registry_from_current_data as get_wave_registry
from src.wave_context import compare_demand_increase, compare_financial_deterioration


def render_page(ctx: PageContext) -> None:
    """Standard section-page entrypoint used by src.app."""
    render_executive_summary(ctx.df, ctx.ui_config.suppressed)


def render_executive_summary(df: pd.DataFrame, suppressed: bool) -> None:
    """Render the Executive Summary page: highlights, KPIs, and narrative.

    Args:
        df: Filtered analysis DataFrame (with derived columns).
        suppressed: If True, show suppression warning and stop (n < K_ANON_THRESHOLD).
    """

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

    # Executive highlights for this (possibly filtered) view
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
            f"**Finance–recruitment link**: Among organisations whose **financial position deteriorated (last 3 months)**, "
            f"{cross['pct_rec_difficulty_if_finance_deteriorated']}% find recruitment difficult, compared with "
            f"{cross['pct_rec_difficulty_if_finance_not_deteriorated']}% among those whose financial position has not deteriorated."
        )

    # Explicit audit trail for how the headline metrics are calculated (filtered-aware)
    with st.expander("Show detailed calculations for these executive highlights"):
        dem_exec = demand_and_outlook(df)
        rec_exec = volunteer_recruitment_analysis(df)
        ret_exec = volunteer_retention_analysis(df)
        wf_exec = workforce_operations(df)
        cross_exec = finance_recruitment_cross(df)

        n_base = len(df)
        demand_count = int(df["demand_direction"].eq("Increased").sum())
        finance_det_count = int(df["financial_direction"].eq("Deteriorated").sum())
        volobj_base = int(df["volobjectives"].notna().sum())
        too_few_count = int(
            df["volobjectives"]
            .isin(["Slightly too few volunteers", "Significantly too few volunteers"])
            .sum()
        )
        vol_rec_base = int(df["vol_rec"].notna().sum())
        vol_rec_hard_count = int(
            df["vol_rec"].isin(["Somewhat difficult", "Extremely difficult"]).sum()
        )
        finance_rising_count = int(df["finance_deteriorated"].sum())
        unplanned_row = wf_exec["actions"][
            wf_exec["actions"]["label"] == "Unplanned use of reserves"
        ]
        unplanned_count = (
            int(unplanned_row["count"].iloc[0]) if not unplanned_row.empty else 0
        )

        st.caption(
            "All values below use the current filtered dataset (n = "
            + str(n_base)
            + " organisations). "
            "Changing sidebar filters updates these numbers. Each metric appears in at least one chart or table on the dashboard."
        )

        st.markdown(
            "- **Demand vs finances (Highlight #2)**  \n"
            f'  - **demand_pct_increased**: organisations where `demand_direction == "Increased"` (from the `demand` Likert question).  \n'
            f"    Formula: **{demand_count} / {n_base} = {dem_exec['demand_pct_increased']}%**.  \n"
            '    _Shown in: Overview page — top KPI tile "Demand increasing" and the stacked bar '
            '"Demand for services has mostly increased" (Recent Experience)._  \n'
            f'  - **financial_pct_deteriorated** (overall position, last 3 months): organisations where `financial_direction == "Deteriorated"`.  \n'
            f"    Formula: **{finance_det_count} / {n_base} = {dem_exec['financial_pct_deteriorated']}%**.  \n"
            '    _Shown in: Overview — KPI "Financial position deteriorated (last 3 months)" and stacked bar; '
            'At-a-Glance. Different from "Finances deteriorated due to rising costs" (Highlight #6, below)._'
        )

        st.markdown(
            "- **Volunteer gaps and recruitment difficulty (Highlight #3)**  \n"
            "  - **pct_too_few**: organisations who answered `volobjectives` and selected "
            "*Slightly too few volunteers* or *Significantly too few volunteers*.  \n"
            f"    Formula: **{too_few_count} / {volobj_base} = {rec_exec['pct_too_few']}%** "
            "(base = those who answered the question).  \n"
            '    _Shown in: Volunteer Recruitment page — "Volunteer Numbers vs. Need" stacked bar and KPI tiles; '
            'At-a-Glance "Key thematic metrics" and infographic._  \n'
            "  - **pct_difficulty** (recruitment): organisations who answered `vol_rec` and selected "
            "*Somewhat difficult* or *Extremely difficult*.  \n"
            f"    Formula: **{vol_rec_hard_count} / {vol_rec_base} = {rec_exec['pct_difficulty']}%** "
            "(base = those who answered the question).  \n"
            '    _Shown in: Volunteer Recruitment page — "Recruitment Difficulty" stacked bar and '
            '"Find recruitment somewhat / very difficult" KPI tile; At-a-Glance._'
        )

        st.markdown(
            "- **Finances deteriorated due to rising costs (Highlight #6)**  \n"
            "  - **finance_deteriorated_pct**: organisations where `financedeteriorate == 'Yes'` "
            "(derived as `finance_deteriorated`).  \n"
            f"    Formula: **{finance_rising_count} / {n_base} = {wf_exec['finance_deteriorated_pct']}%**.  \n"
            "    _Shown in: Workforce & Operations page — first KPI tile "
            '"Finances deteriorated due to rising costs"; Trends & Waves trend table._  \n'
            "  - **Unplanned use of reserves** (count used in the same highlight): organisations that "
            "selected this option in the actions multi-select.  \n"
            f"    Count: **{unplanned_count}** organisations.  \n"
            "    _Shown in: Workforce & Operations and Concerns & Risks pages — "
            '"Actions Taken Due to Rising Costs" horizontal bar chart and data table._'
        )

        if cross_exec:
            det_ans = (
                df["financial_direction"].eq("Deteriorated") & df["vol_rec"].notna()
            )
            not_det_ans = (
                (~df["financial_direction"].eq("Deteriorated"))
                & df["financial_direction"].notna()
                & df["vol_rec"].notna()
            )
            rec_hard = df["vol_rec"].isin(["Somewhat difficult", "Extremely difficult"])
            det_hard = int(rec_hard[det_ans].sum())
            not_det_hard = int(rec_hard[not_det_ans].sum())
            det_ans_n = int(det_ans.sum())
            not_det_ans_n = int(not_det_ans.sum())
            n_det = cross_exec["n_finance_deteriorated"]
            n_not_det = cross_exec["n_finance_not_deteriorated"]

            # Small audit-table so the raw counts are visible
            cross_rows = [
                {
                    "Finance group": "Financial position deteriorated (3 mth)",
                    "Orgs in group (n)": n_det,
                    "Answered recruitment (vol_rec)": det_ans_n,
                    "Recruitment difficult (count)": det_hard,
                },
                {
                    "Finance group": "Financial position not deteriorated (3 mth)",
                    "Orgs in group (n)": n_not_det,
                    "Answered recruitment (vol_rec)": not_det_ans_n,
                    "Recruitment difficult (count)": not_det_hard,
                },
            ]
            # Let pandas infer dtypes (mix of string + integer columns)
            cross_df = pd.DataFrame(cross_rows)

            st.markdown(
                "- **Finance–recruitment cross metric (optional Highlight #7 and info box)**  \n"
                f"  - Highlight #7 reports **n={n_det} vs {n_not_det}**: the number of organisations in each group "
                "(financial position deteriorated vs not, last 3 months).  \n"
                "  - The percentages use only those who answered the recruitment difficulty question (`vol_rec`).  \n"
                "  - **Financial position deteriorated (3 mth)** group: "
                f"{n_det} organisations, {det_ans_n} answered `vol_rec` → **{det_hard} / {det_ans_n} "
                f"= {cross_exec['pct_rec_difficulty_if_finance_deteriorated']}%** find recruitment difficult.  \n"
                "  - **Financial position not deteriorated (3 mth)** group: "
                f"{n_not_det} organisations, {not_det_ans_n} answered `vol_rec` → **{not_det_hard} / {not_det_ans_n} "
                f"= {cross_exec['pct_rec_difficulty_if_finance_not_deteriorated']}%** find recruitment difficult.  \n"
                "  - The difference between these two percentages underpins the statement that recruitment challenges "
                "are higher where financial position has deteriorated (last 3 months).  \n"
                "  _Components shown in: Overview / Workforce & Operations (finance tiles); Volunteer Recruitment page "
                '("Recruitment Difficulty" chart and table — the difficulty count used here is split by finance group '
                "in this Executive Summary); Concerns & Risks (concerns chart). The cross comparison itself is only in "
                "this Executive Summary and the info box above._"
            )

            st.dataframe(
                cross_df,
                hide_index=True,
                width="stretch",
            )
        else:
            st.markdown(
                "- **Finance–recruitment cross metric**  \n"
                "  - Not shown here because the filtered sample is too small for a reliable comparison "
                "(we require minimum counts in each finance group and among those answering the `vol_rec` question)."
            )

    st.divider()
    st.subheader("Wave context across waves")
    registry = get_wave_registry(df)
    for label in registry.list_waves():
        wave_ctx = registry.get(label)
        bullet_lines = "".join(
            f"<li>{line}</li>" for line in wave_ctx.executive_context_callouts()
        )
        st.markdown(
            f"<div style='border-left:4px solid {WCVA_BRAND['blue']};"
            f"background:#F7F8FA;padding:12px 16px;margin:8px 0;border-radius:4px;'>"
            f"<strong>{wave_ctx.meta.wave_label}</strong> "
            f"<span style='color:#555'>(n={wave_ctx.meta.wave_response_count})</span>"
            "<ul style='margin-top:6px;padding-left:18px;color:#333;font-size:0.9rem;'>"
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
        "Over the same period, the share reporting finances deteriorated due to rising costs shifted from "
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
                seg_rows.append(
                    {
                        "Size": f"{size} (n={d['n']})",
                        "Demand increased %": d["pct_demand_increased"],
                        "Financial position deteriorated (3 mth) %": d[
                            "pct_finance_deteriorated"
                        ],
                        "Vol. recruitment difficulty %": d["pct_vol_rec_difficulty"],
                        "Vol. retention difficulty %": d["pct_vol_ret_difficulty"],
                        "Too few volunteers %": d["pct_too_few_vols"],
                    }
                )
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
                "Financial position deteriorated (3 mth) %": d[
                    "pct_finance_deteriorated"
                ],
                "Vol. recruitment difficulty %": d["pct_vol_rec_difficulty"],
                "Too few volunteers %": d["pct_too_few_vols"],
            }
            for name, d in sorted(act_data.items(), key=lambda x: -x[1]["n"])[:10]
        ]
        if act_rows:
            st.dataframe(pd.DataFrame(act_rows), hide_index=True, width="stretch")
        st.caption(
            "Top 10 activities by sample size. Smaller segments are also informative."
        )

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
        funding_vol_sentence = (
            f"Only {signpost_pct}% of organisations offer financial signposting."
        )
    else:
        funding_vol_sentence = "Expenses coverage is widespread but financial signposting remains relatively rare."

    st.markdown(f"""
1. **Invest in volunteering infrastructure** — Organisations are trying but getting low response. Centralised campaigns via TSSW/CVCs could boost reach.

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


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
