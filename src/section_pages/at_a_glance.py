# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import WCVA_BRAND, get_app_ui_config
from src.eda import (
    demand_and_outlook,
    volunteer_recruitment_analysis,
    volunteer_retention_analysis,
)
from src.infographic import render_at_a_glance_infographic
from src.narratives import (
    demand_finance_scissor_phrase,
    recruitment_vs_retention_phrase,
)
from src.page_context import PageContext
from src.wave_context import get_wave_registry


# Wave 1 vs "This view" (card values) so numbers match the cards and definitions are clear
def _delta_arrow(old: float, new: float, *, higher_is_good: bool) -> str:
    """Return a coloured arrow HTML snippet.

    - ▲ / ▼ always show direction of change (higher vs lower than Wave 1).
    - Colour reflects whether that change is positive or a pressure
      for the metric in question.
    """
    delta = round(float(new) - float(old), 1)
    if abs(delta) < 0.1:
        return f"<span style='color:{WCVA_BRAND['mid_grey']}'>●</span>"

    went_up = delta > 0
    symbol = "▲" if went_up else "▼"
    is_positive_change = went_up if higher_is_good else not went_up
    colour = WCVA_BRAND["amber"] if is_positive_change else WCVA_BRAND["coral"]
    sign = "+" if delta > 0 else ""
    delta_str = f"{delta:.1f}".rstrip("0").rstrip(".")
    return (
        f"<span style='color:{colour};font-weight:700'>{symbol}</span> "
        f"({sign}{delta_str} pts)"
    )


def render_page(ctx: PageContext) -> None:
    """Standard section-page entrypoint used by src.app."""
    render_at_a_glance(
        ctx.df,
        ctx.n,
        ctx.ui_config.accessible_mode,
    )


def render_at_a_glance(df: pd.DataFrame, n: int, accessible_mode: bool) -> None:
    """Render the At-a-Glance page: infographic, KPI cards, and narrative.

    Args:
        df: Filtered analysis DataFrame.
        n: Filtered row count (for subtitles and suppression).
        accessible_mode: Whether to use accessible palette in infographic.
    """
    st.title("State of Volunteering in Wales — At a Glance")
    st.caption("Baromedr Cymru — Wave 2 (organisational survey)")

    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning(
            "Results suppressed due to small sample size. Adjust filters to see data."
        )
        st.stop()

    dem = demand_and_outlook(df)
    rec = volunteer_recruitment_analysis(df)
    ret = volunteer_retention_analysis(df)

    # Enrich the infographic inputs with previous-wave benchmarks so that
    # trend arrows and colours reflect the longer-term direction of travel.
    # These benchmarks are wave-level (all organisations) rather than
    # filter-specific, so they provide a stable reference even when filters
    # are applied.
    registry = get_wave_registry(df)
    first_wave, latest_wave = registry.first_and_latest()

    dem["demand_pct_increased_prev"] = (
        first_wave.demand.headline.increasing_demand_for_services_pct
    )
    # Do not set financial_pct_deteriorated_prev from Wave 1: Wave 1 only has
    # "deteriorated due to rising costs", which is a different question from this
    # card's "financial position deteriorated (last 3 months)". Comparing them
    # would mix two measures. Leave unset so the infographic shows no trend comparison.
    dem["financial_pct_deteriorated_prev"] = None

    too_few_prev = first_wave.workforce.headline.too_few_volunteers_pct
    rec_diff_prev = (
        first_wave.workforce.headline.face_volunteer_recruitment_difficulties_pct
    )
    ret_diff_prev = (
        first_wave.workforce.headline.face_volunteer_retention_difficulties_pct
    )

    # Only attach previous values where a benchmark exists; this keeps the
    # infographic robust even if earlier waves lack a particular metric.
    if too_few_prev is not None:
        rec["pct_too_few_prev"] = too_few_prev
    if rec_diff_prev is not None:
        rec["pct_difficulty_prev"] = rec_diff_prev
    if ret_diff_prev is not None:
        ret["pct_difficulty_prev"] = ret_diff_prev

    render_at_a_glance_infographic(
        n,
        dem,
        rec,
        ret,
        height=720,
        accessible=accessible_mode,
    )
    st.caption(
        "Poster-style summary of how rising demand, finances, and volunteer gaps "
        "interact in this filtered view of the survey. "
        "Arrows show whether each percentage is higher or lower than the previous wave; "
        "colours and short labels indicate whether that change represents a pressure or a positive."
    )

    # Show how these At-a-Glance KPIs are calculated (same pattern as Overview)
    with st.expander("Show how these At-a-Glance KPIs are calculated"):
        demand_inc_count = int(df["demand_direction"].eq("Increased").sum())
        demand_base = int(df["demand_direction"].notna().sum())
        finance_det_count = int(df["financial_direction"].eq("Deteriorated").sum())
        finance_base = int(df["financial_direction"].notna().sum())
        volobj_base = int(df["volobjectives"].notna().sum())
        too_few_count = int(
            df["volobjectives"]
            .isin(["Slightly too few volunteers", "Significantly too few volunteers"])
            .sum()
        )
        vol_rec_base = int(df["vol_rec"].notna().sum())
        vol_rec_hard = int(
            df["vol_rec"].isin(["Somewhat difficult", "Extremely difficult"]).sum()
        )
        vol_ret_base = int(df["vol_ret"].notna().sum())
        vol_ret_hard = int(
            df["vol_ret"].isin(["Somewhat difficult", "Extremely difficult"]).sum()
        )

        at_glance_rows = [
            {
                "Metric": "Share reporting increased demand",
                "Column / question": "demand_direction",
                "Numerator (count)": demand_inc_count,
                "Denominator (answered)": demand_base,
                "Percentage": dem["demand_pct_increased"],
            },
            {
                "Metric": "Share reporting financial position deteriorated (last 3 months)",
                "Column / question": "financial_direction (Likert)",
                "Numerator (count)": finance_det_count,
                "Denominator (answered)": finance_base,
                "Percentage": dem["financial_pct_deteriorated"],
            },
            {
                "Metric": "Share with too few volunteers",
                "Column / question": "volobjectives",
                "Numerator (count)": too_few_count,
                "Denominator (answered)": volobj_base,
                "Percentage": rec["pct_too_few"],
            },
            {
                "Metric": "Share finding recruitment difficult",
                "Column / question": "vol_rec (Likert)",
                "Numerator (count)": vol_rec_hard,
                "Denominator (answered)": vol_rec_base,
                "Percentage": rec["pct_difficulty"],
            },
            {
                "Metric": "Share finding retention difficult",
                "Column / question": "vol_ret (Likert)",
                "Numerator (count)": vol_ret_hard,
                "Denominator (answered)": vol_ret_base,
                "Percentage": ret["pct_difficulty"],
            },
        ]
        at_glance_df = pd.DataFrame(at_glance_rows)

        st.markdown(
            "The cards above use the same definitions and bases as the **Overview** and **Executive Summary**. "
            "Percentages are calculated only over organisations that answered each question. "
            "The table below shows the exact counts and bases for this filtered view."
        )
        st.dataframe(at_glance_df, hide_index=True, width="stretch")

    with st.expander("Wave 1 vs this view (same definitions as the cards)"):
        # "This view" = current filtered card values so they always match the infographic
        d_this = dem["demand_pct_increased"]
        f_this = dem["financial_pct_deteriorated"]
        tf_this = rec["pct_too_few"]
        rec_this = rec["pct_difficulty"]
        ret_this = ret["pct_difficulty"]

        d_old = first_wave.demand.headline.increasing_demand_for_services_pct
        tf_old = first_wave.workforce.headline.too_few_volunteers_pct
        rec_old = (
            first_wave.workforce.headline.face_volunteer_recruitment_difficulties_pct
        )
        ret_old = (
            first_wave.workforce.headline.face_volunteer_retention_difficulties_pct
        )
        # Wave 1 finance headline is "deteriorated due to rising costs", not Likert; card uses Likert
        f_old_rising = first_wave.finance.headline.financial_position_deteriorated_due_to_rising_costs_pct

        st.markdown(
            "**This view** = the same percentages as the cards above (current filters). "
            "**Wave 1** = registry benchmarks. For demand, too few volunteers, and recruitment/retention difficulty, "
            "the definition matches. For finances, the card uses *financial position deteriorated* (Likert); "
            "Wave 1 only has *deteriorated due to rising costs* (different question), so that row is labelled below."
        )

        bullets = [
            (
                "Share reporting increased demand",
                d_old,
                d_this,
                _delta_arrow(d_old, d_this, higher_is_good=False),
            ),
        ]

        if tf_old is not None:
            bullets.append(
                (
                    "Share with too few volunteers",
                    tf_old,
                    tf_this,
                    _delta_arrow(tf_old, tf_this, higher_is_good=False),
                )
            )
        bullets.append(
            (
                "Share finding recruitment difficult",
                rec_old,
                rec_this,
                _delta_arrow(rec_old, rec_this, higher_is_good=False),
            )
        )
        bullets.append(
            (
                "Share finding retention difficult",
                ret_old,
                ret_this,
                _delta_arrow(ret_old, ret_this, higher_is_good=False),
            )
        )

        def _pct_disp(x) -> str:
            if x is None:
                return "—"
            v = round(float(x), 1)
            return str(int(v)) if v == int(v) else str(v)

        lines = []
        for label, old, new, arrow_html in bullets:
            lines.append(
                f"<li><strong>{label}</strong>: Wave 1 {_pct_disp(old)}% → This view {_pct_disp(new)}% {arrow_html}</li>"
            )

        st.markdown(
            "<ul style='margin-top:4px;padding-left:18px;font-size:0.9rem;color:#333;'>"
            + "".join(lines)
            + "</ul>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "**Finances:** This view uses *financial position deteriorated* (Likert, last 3 months): "
            f"**{_pct_disp(f_this)}%**. Wave 1 reported *deteriorated due to rising costs* (different question): "
            f"**{_pct_disp(f_old_rising)}%** — not directly comparable."
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
            {
                "Metric": "Share reporting increased demand",
                "Value": f"{dem['demand_pct_increased']}%",
            },
            {
                "Metric": "Share reporting financial position deteriorated (last 3 months)",
                "Value": f"{dem['financial_pct_deteriorated']}%",
            },
            {
                "Metric": "Share with too few volunteers",
                "Value": f"{rec['pct_too_few']}%",
            },
            {
                "Metric": "Share finding recruitment difficult",
                "Value": f"{rec['pct_difficulty']}%",
            },
            {
                "Metric": "Share finding retention difficult",
                "Value": f"{ret['pct_difficulty']}%",
            },
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
        "- Among organisations whose financial position has deteriorated (last 3 months), is recruitment difficulty higher than for those with stable finances?\n"
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


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
