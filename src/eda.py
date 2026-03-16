# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
Exploratory data analysis functions for Baromedr Cymru Wave 2.

Each function takes a (possibly filtered) DataFrame (with columns from
data_loader derived output) and returns structured results (dicts, DataFrames)
ready for charting or display. Percentages use non-missing bases per question
where applicable. Key functions:

- profile_summary: Org size, legal form, geography, LA context, volunteer/staff pct.
- demand_and_outlook: Demand/finance/operating distributions and headline pcts.
- volunteer_recruitment_analysis: Recruitment difficulty, barriers, methods (by segment).
- volunteer_retention_analysis: Retention difficulty, barriers (by segment).
- workforce_operations: Staff/vol recruitment and retention, concerns, actions, reserves.
- volunteer_demographics: Demographics presence and change matrix.
- volunteering_types: Type usage and earned settlement.
- cross_segment_analysis: Metrics by org_size, scope, main activity.
- finance_recruitment_cross: Recruitment difficulty by financial deterioration (or None).
- executive_highlights: Ranked list of dicts for executive summary.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config import (
    ACTIONS_LABELS,
    CONCERNS_LABELS,
    DEMAND_ORDER,
    DIFFICULTY_ORDER,
    EARNED_SETTLEMENT_ORDER,
    EXPECT_DEMAND_ORDER,
    EXPECT_FINANCIAL_ORDER,
    FINANCIAL_ORDER,
    OPERATING_ORDER,
    ORG_SIZE_ORDER,
    REC_BARRIERS_LABELS,
    REC_METHODS_LABELS,
    RET_BARRIERS_LABELS,
    SHORTAGE_AFFECT_LABELS,
    VOL_DEM_CHANGE_LABELS,
    VOL_DEM_LABELS,
    VOL_OBJECTIVES_ORDER,
    VOL_OFFER_LABELS,
    VOL_TYPEUSE_LABELS,
    VOL_TYPEUSE_ORDER,
    YES_NO_ORDER,
)
from src.data_loader import (
    count_multiselect,
    count_multiselect_by_segment,
    load_la_context,
)


def _value_counts_ordered(series: pd.Series, order: list[str]) -> pd.DataFrame:
    """Value counts in a fixed order with pct over non-missing base.

    Args:
        series: Categorical series (e.g. demand, financial).
        order: Ordered list of category values; missing categories get count 0.

    Returns:
        DataFrame with columns value, count, pct (pct sums to 100 over order).
    """
    vc = series.value_counts()
    n = series.notna().sum()
    rows = []
    for val in order:
        count = int(vc.get(val, 0))
        rows.append(
            {"value": val, "count": count, "pct": round(100 * count / n, 1) if n else 0}
        )
    return pd.DataFrame(rows)


def _share_true(series: pd.Series) -> float:
    """Return percentage of True values over non-missing base.

    Design: percentages are over series.notna() so that KPI tiles, charts,
    and narratives stay consistent when some organisations skip a question.

    Args:
        series: Boolean or truthy series.

    Returns:
        Float in [0, 100] or 0.0 if no non-missing values.
    """
    base = int(series.notna().sum())
    if base == 0:
        return 0.0
    return round(100 * series.sum() / base, 1)


# ---------------------------------------------------------------------------
# 1. Profile summary
# ---------------------------------------------------------------------------


def profile_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Return organisational profile summary for Overview and similar pages.

    Includes: n, org_size, legalform, wales_scope, mainactivity, la_distribution,
    region_distribution, la_context (joined), has_volunteers_pct, has_paid_staff_pct,
    social_enterprise_pct (if column present).

    Args:
        df: DataFrame with org_size, legalform, location_la_primary, peoplevol,
            paidworkforce, and optionally socialenterprise, region.

    Returns:
        Dict with keys above; percentages are 0.0 when base is zero or column missing.
    """
    n = len(df)

    # Basic distributions used throughout the app
    org_size = (
        df["org_size"]
        .value_counts()
        .reindex(ORG_SIZE_ORDER)
        .fillna(0)
        .astype(int)
        .to_dict()
    )
    legalform = df["legalform"].value_counts().head(6).to_dict()
    wales_scope = df["wales_scope"].value_counts().to_dict()
    mainactivity = df["mainactivity"].value_counts().head(10).to_dict()
    la_distribution = df["location_la_primary"].value_counts().to_dict()
    region_distribution = df["region"].value_counts().to_dict()

    # Local-authority context: join sample counts onto population/org counts
    la_ctx = load_la_context()
    la_counts = (
        df["location_la_primary"]
        .value_counts()
        .rename("sample_count")
        .rename_axis("local_authority")
        .reset_index()
    )
    la_merged = la_ctx.merge(la_counts, on="local_authority", how="left")
    la_merged["sample_count"] = la_merged["sample_count"].fillna(0).astype(int)

    total_sample = float(n) if n else 1.0
    total_pop = float(la_merged["population_2024"].sum()) or 1.0

    la_merged["sample_share_pct"] = la_merged["sample_count"] / total_sample * 100.0
    la_merged["pop_share_pct"] = la_merged["population_2024"] / total_pop * 100.0
    la_merged["sample_per_100k"] = (
        la_merged["sample_count"] / la_merged["population_2024"] * 100000.0
    )
    la_merged["orgs_per_10k_pop"] = (
        la_merged["est_vcse_orgs"] / la_merged["population_2024"] * 10000.0
    )
    # Over/under-representation index (100 = proportional to population)
    la_merged["representation_index"] = (
        (la_merged["sample_share_pct"] / la_merged["pop_share_pct"])
        .replace([float("inf"), -float("inf")], 0.0)
        .fillna(0.0)
    )

    # Share of organisations reporting any volunteers.
    # We treat strictly positive volunteer counts as having volunteers.
    if "peoplevol" in df.columns and n:
        has_volunteers_pct = round(
            100 * (df["peoplevol"].fillna(0) > 0).sum() / n,
            1,
        )
    else:
        has_volunteers_pct = 0

    # Some smaller test DataFrames may not include all profile columns;
    # in that case we fall back to 0% rather than raising a KeyError.
    if "socialenterprise" in df.columns and n:
        social_enterprise_pct = round(
            100 * (df["socialenterprise"] == "Yes").sum() / n,
            1,
        )
    else:
        social_enterprise_pct = 0

    if "paidworkforce" in df.columns and n:
        has_paid_staff_pct = round(
            100 * (df["paidworkforce"] == "Yes").sum() / n,
            1,
        )
    else:
        has_paid_staff_pct = 0

    return {
        "n": n,
        "org_size": org_size,
        "legalform": legalform,
        "wales_scope": wales_scope,
        "mainactivity": mainactivity,
        "la_distribution": la_distribution,
        "region_distribution": region_distribution,
        "la_context": la_merged.to_dict(orient="records"),
        "est_vcse_orgs": la_merged[["local_authority", "est_vcse_orgs"]],
        "social_enterprise_pct": social_enterprise_pct,
        "has_paid_staff_pct": has_paid_staff_pct,
        "has_volunteers_pct": has_volunteers_pct,
        "median_employees": df["peopleemploy"].median(),
        "median_volunteers": df["peoplevol"].median(),
    }


# ---------------------------------------------------------------------------
# 2. Demand and outlook
# ---------------------------------------------------------------------------


def demand_and_outlook(df: pd.DataFrame) -> dict[str, Any]:
    """Aggregates for demand, finances, and operating outlook.

    Returns value_counts DataFrames (demand, financial, operating, workforce_change,
    expect_demand, expect_financial) and headline percentages: demand_pct_increased,
    financial_pct_deteriorated, operating_pct_likely. Empty df yields 0.0 for pcts.

    Args:
        df: DataFrame with demand, financial, operating, expectdemand, expectfinancial,
            workforce, and derived demand_direction, financial_direction.

    Returns:
        Dict with keys above; pct values in [0, 100].
    """
    n = len(df)

    demand = (
        _value_counts_ordered(df["demand"], DEMAND_ORDER)
        if "demand" in df.columns
        else _value_counts_ordered(pd.Series(dtype="object"), DEMAND_ORDER)
    )  # noqa: E501
    financial = (
        _value_counts_ordered(df["financial"], FINANCIAL_ORDER)
        if "financial" in df.columns
        else _value_counts_ordered(pd.Series(dtype="object"), FINANCIAL_ORDER)
    )  # noqa: E501
    operating = (
        _value_counts_ordered(df["operating"], OPERATING_ORDER)
        if "operating" in df.columns
        else _value_counts_ordered(pd.Series(dtype="object"), OPERATING_ORDER)
    )  # noqa: E501
    workforce_change = (
        _value_counts_ordered(df["workforce"], DEMAND_ORDER)
        if "workforce" in df.columns
        else _value_counts_ordered(pd.Series(dtype="object"), DEMAND_ORDER)
    )  # noqa: E501
    expect_demand = (
        _value_counts_ordered(df["expectdemand"], EXPECT_DEMAND_ORDER)
        if "expectdemand" in df.columns
        else _value_counts_ordered(pd.Series(dtype="object"), EXPECT_DEMAND_ORDER)
    )  # noqa: E501
    expect_financial = (
        _value_counts_ordered(df["expectfinancial"], EXPECT_FINANCIAL_ORDER)
        if "expectfinancial" in df.columns
        else _value_counts_ordered(pd.Series(dtype="object"), EXPECT_FINANCIAL_ORDER)
    )  # noqa: E501

    if n == 0:
        demand_pct_increased = 0.0
        financial_pct_deteriorated = 0.0
        operating_pct_likely = 0.0
    else:
        demand_pct_increased = round(
            100 * df["demand_direction"].eq("Increased").sum() / n,
            1,
        )
        financial_pct_deteriorated = round(
            100 * df["financial_direction"].eq("Deteriorated").sum() / n,
            1,
        )
        operating_pct_likely = round(
            100 * df["operating"].isin(["Very likely", "Quite likely"]).sum() / n,
            1,
        )

    return {
        "demand": demand,
        "financial": financial,
        "operating": operating,
        "workforce_change": workforce_change,
        "expect_demand": expect_demand,
        "expect_financial": expect_financial,
        "demand_pct_increased": demand_pct_increased,
        "financial_pct_deteriorated": financial_pct_deteriorated,
        "operating_pct_likely": operating_pct_likely,
    }


# ---------------------------------------------------------------------------
# 3. Volunteer recruitment
# ---------------------------------------------------------------------------


def volunteer_recruitment_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Return volunteer recruitment metrics: shortage, difficulty, barriers, methods (and by-segment tables)."""
    n = len(df)
    shortage_series = df["has_vol_rec_difficulty"]
    # For Likert-based difficulty, use only respondents who answered the question
    vol_rec_series = df["vol_rec"]
    likert_base = int(vol_rec_series.notna().sum())
    likert_hard = int(
        vol_rec_series.isin(["Somewhat difficult", "Extremely difficult"]).sum()
    )
    return {
        "n": n,
        "shortage_vol_rec": _value_counts_ordered(df["shortage_vol_rec"], YES_NO_ORDER),
        "vol_rec_difficulty": _value_counts_ordered(df["vol_rec"], DIFFICULTY_ORDER),
        "vol_objectives": _value_counts_ordered(
            df["volobjectives"], VOL_OBJECTIVES_ORDER
        ),
        "rec_methods": count_multiselect(df, REC_METHODS_LABELS),
        "rec_barriers": count_multiselect(df, REC_BARRIERS_LABELS),
        "rec_barriers_by_size": count_multiselect_by_segment(
            df, REC_BARRIERS_LABELS, "org_size"
        ),
        "rec_methods_by_size": count_multiselect_by_segment(
            df, REC_METHODS_LABELS, "org_size"
        ),
        # Share finding recruitment somewhat or extremely difficult (Likert-based, non-missing base)
        "difficulty_base": likert_base,
        "pct_difficulty": (
            round(100 * likert_hard / likert_base, 1) if likert_base else 0
        ),
        # Share explicitly reporting a shortage recruiting volunteers (non-missing base)
        "pct_shortage": _share_true(shortage_series),
        "pct_too_few": (
            lambda series: (
                round(
                    100
                    * series.isin(
                        [
                            "Slightly too few volunteers",
                            "Significantly too few volunteers",
                        ]
                    ).sum()
                    / series.notna().sum(),
                    1,
                )
                if series.notna().sum()
                else 0
            )
        )(df["volobjectives"]),
    }


# ---------------------------------------------------------------------------
# 4. Volunteer retention
# ---------------------------------------------------------------------------


def volunteer_retention_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Return volunteer retention metrics: difficulty, barriers (and by-segment tables)."""
    n = len(df)
    shortage_series = df["has_vol_ret_difficulty"]
    # For Likert-based difficulty, use only respondents who answered the question
    vol_ret_series = df["vol_ret"]
    likert_base = int(vol_ret_series.notna().sum())
    likert_hard = int(
        vol_ret_series.isin(["Somewhat difficult", "Extremely difficult"]).sum()
    )
    return {
        "n": n,
        "shortage_vol_ret": _value_counts_ordered(df["shortage_vol_ret"], YES_NO_ORDER),
        "vol_ret_difficulty": _value_counts_ordered(df["vol_ret"], DIFFICULTY_ORDER),
        "ret_barriers": count_multiselect(df, RET_BARRIERS_LABELS),
        "vol_offer": count_multiselect(df, VOL_OFFER_LABELS),
        "ret_barriers_by_size": count_multiselect_by_segment(
            df, RET_BARRIERS_LABELS, "org_size"
        ),
        "vol_offer_by_size": count_multiselect_by_segment(
            df, VOL_OFFER_LABELS, "org_size"
        ),
        # Share finding retention somewhat or extremely difficult (Likert-based, non-missing base)
        "difficulty_base": likert_base,
        "pct_difficulty": (
            round(100 * likert_hard / likert_base, 1) if likert_base else 0
        ),
        # Share explicitly reporting a shortage retaining volunteers (non-missing base)
        "pct_shortage": _share_true(shortage_series),
    }


# ---------------------------------------------------------------------------
# 5. Workforce and operations
# ---------------------------------------------------------------------------


def workforce_operations(df: pd.DataFrame) -> dict[str, Any]:
    """Return workforce and operations metrics: staff/vol recruitment and retention, concerns, actions, reserves."""
    n = len(df)
    with_staff = df[df["paidworkforce"] == "Yes"]
    n_staff = len(with_staff)

    staff_rec_difficulty = _value_counts_ordered(
        with_staff["shortage_staff_rec"], YES_NO_ORDER
    )
    staff_ret_difficulty = _value_counts_ordered(
        with_staff["shortage_staff_ret"], YES_NO_ORDER
    )

    # Among organisations with paid staff, share reporting recruitment/retention difficulties.
    if n_staff:
        rec_yes_row = staff_rec_difficulty[staff_rec_difficulty["value"] == "Yes"]
        ret_yes_row = staff_ret_difficulty[staff_ret_difficulty["value"] == "Yes"]
        staff_rec_difficulty_pct = (
            float(rec_yes_row["pct"].iloc[0]) if not rec_yes_row.empty else 0.0
        )
        staff_ret_difficulty_pct = (
            float(ret_yes_row["pct"].iloc[0]) if not ret_yes_row.empty else 0.0
        )
    else:
        staff_rec_difficulty_pct = 0.0
        staff_ret_difficulty_pct = 0.0

    # Across all organisations, share reporting volunteer recruitment/retention difficulties
    # Use non-missing bases to stay consistent with recruitment/retention analyses.
    vol_rec_difficulty_pct = _share_true(df["has_vol_rec_difficulty"])
    vol_ret_difficulty_pct = _share_true(df["has_vol_ret_difficulty"])

    return {
        "n": n,
        "n_with_staff": n_staff,
        "staff_rec_difficulty": staff_rec_difficulty,
        "staff_ret_difficulty": staff_ret_difficulty,
        "staff_rec_difficulty_pct": staff_rec_difficulty_pct,
        "staff_ret_difficulty_pct": staff_ret_difficulty_pct,
        "vol_rec_difficulty_pct": vol_rec_difficulty_pct,
        "vol_ret_difficulty_pct": vol_ret_difficulty_pct,
        "shortage_affect": count_multiselect(df, SHORTAGE_AFFECT_LABELS),
        "concerns": count_multiselect(df, CONCERNS_LABELS),
        "actions": count_multiselect(df, ACTIONS_LABELS),
        "finance_deteriorated_pct": round(
            100 * df["finance_deteriorated"].sum() / (n or 1), 1
        ),
        "reserves_yes_pct": round(100 * (df["reserves"] == "Yes").sum() / (n or 1), 1),
        "using_reserves_pct": (
            round(
                100
                * (df["usingreserves"] == "Yes").sum()
                / df["reserves"].eq("Yes").sum(),
                1,
            )
            if df["reserves"].eq("Yes").sum() > 0
            else 0
        ),
        "median_months_reserves": df["monthsreserves"].median(),
        "workforce_change": _value_counts_ordered(df["workforce"], DEMAND_ORDER),
    }


# ---------------------------------------------------------------------------
# 6. Volunteer demographics
# ---------------------------------------------------------------------------


def volunteer_demographics(df: pd.DataFrame) -> dict[str, Any]:
    """Return volunteer demographics presence and change matrix by demographic group."""
    dem_presence = count_multiselect(df, VOL_DEM_LABELS)

    # Build a change matrix: rows = demographic group, cols = change category
    change_order = [
        "Increased a lot",
        "Increased a little",
        "Stayed the same",
        "Decreased a little",
        "Decreased a lot",
        "Not applicable",
    ]
    change_matrix = []
    for col, label in VOL_DEM_CHANGE_LABELS.items():
        if col not in df.columns:
            continue
        vc = df[col].value_counts()
        row = {"group": label}
        for cat in change_order:
            row[cat] = int(vc.get(cat, 0))
        change_matrix.append(row)

    return {
        "n": len(df),
        "dem_presence": dem_presence,
        "change_matrix": pd.DataFrame(change_matrix),
        "change_order": change_order,
        "vol_time": _value_counts_ordered(
            df["vol_time"],
            [
                "Increased a lot",
                "Increased a little",
                "Stayed the same",
                "Decreased a little",
                "Decreased a lot",
                "Don't know",
            ],
        ),
    }


# ---------------------------------------------------------------------------
# 7. Volunteering types and earned settlement
# ---------------------------------------------------------------------------


def volunteering_types(df: pd.DataFrame) -> dict[str, Any]:
    """Return volunteering types usage and earned settlement / capacity distributions."""
    type_data = {}
    for col, label in VOL_TYPEUSE_LABELS.items():
        if col in df.columns:
            type_data[label] = _value_counts_ordered(df[col], VOL_TYPEUSE_ORDER)

    earned_settlement = (
        _value_counts_ordered(df["earnedsettlement"], EARNED_SETTLEMENT_ORDER)
        if "earnedsettlement" in df.columns
        else pd.DataFrame(columns=["value", "count", "pct"])
    )
    settlement_capacity = (
        df["settlement_capacity"].value_counts().to_dict()
        if "settlement_capacity" in df.columns
        else {}
    )

    return {
        "n": len(df),
        "type_data": type_data,
        "earned_settlement": earned_settlement,
        "settlement_capacity": settlement_capacity,
    }


# ---------------------------------------------------------------------------
# 8. Cross-segment analysis
# ---------------------------------------------------------------------------


def _segment_metrics(subset: pd.DataFrame, n: int) -> dict:
    """Shared metrics for a subset (n = len(subset))."""
    volobj = subset["volobjectives"]
    volobj_base = int(volobj.notna().sum())
    rec_diff = subset["has_vol_rec_difficulty"]
    ret_diff = subset["has_vol_ret_difficulty"]
    return {
        "n": n,
        # Percentages use non-missing bases per-metric; this keeps segment tables
        # aligned with the main KPIs and avoids denominator confusion.
        "pct_vol_rec_difficulty": _share_true(rec_diff),
        "pct_vol_ret_difficulty": _share_true(ret_diff),
        "pct_demand_increased": _share_true(subset["demand_direction"].eq("Increased")),
        "pct_finance_deteriorated": _share_true(
            subset["financial_direction"].eq("Deteriorated")
        ),
        "pct_too_few_vols": (
            round(
                100
                * volobj.isin(
                    ["Slightly too few volunteers", "Significantly too few volunteers"]
                ).sum()
                / volobj_base,
                1,
            )
            if volobj_base
            else 0
        ),
    }


def cross_segment_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Key metrics broken down by org_size, scope, and main activity."""
    segments = {}
    min_n = 3  # avoid tiny segments

    for seg_col, seg_name in [
        ("org_size", "Organisation Size"),
        ("wales_scope", "Geographic Scope"),
        ("mainactivity", "Main activity"),
    ]:
        if seg_col not in df.columns:
            continue
        seg_data = {}
        for seg_val in df[seg_col].dropna().unique():
            subset = df[df[seg_col] == seg_val]
            n = len(subset)
            if n < min_n:
                continue
            seg_data[seg_val] = _segment_metrics(subset, n)
        segments[seg_name] = seg_data

    return segments


def finance_recruitment_cross(df: pd.DataFrame) -> dict[str, Any] | None:
    """
    Among orgs whose financial position deteriorated (last 3 mth) vs not, what % find recruitment difficult?
    Returns None if counts are too small for a sensible comparison.
    """
    n = len(df)
    if n < 10:
        return None
    det = df["financial_direction"] == "Deteriorated"
    not_det = ~det & df["financial_direction"].notna()
    rec_hard = df["vol_rec"].isin(["Somewhat difficult", "Extremely difficult"])
    n_det = det.sum()
    n_not_det = not_det.sum()
    if n_det < 3 or n_not_det < 3:
        return None
    # Among those who answered the recruitment difficulty question
    det_answered = det & df["vol_rec"].notna()
    not_det_answered = not_det & df["vol_rec"].notna()
    pct_det = round(100 * rec_hard[det_answered].sum() / max(1, det_answered.sum()), 1)
    pct_not_det = round(
        100 * rec_hard[not_det_answered].sum() / max(1, not_det_answered.sum()), 1
    )
    return {
        "pct_rec_difficulty_if_finance_deteriorated": pct_det,
        "pct_rec_difficulty_if_finance_not_deteriorated": pct_not_det,
        "n_finance_deteriorated": int(n_det),
        "n_finance_not_deteriorated": int(n_not_det),
    }


# ---------------------------------------------------------------------------
# 9. Executive summary highlights
# ---------------------------------------------------------------------------


def executive_highlights(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return a ranked list of key insights for the executive summary."""
    n = len(df)
    rec = volunteer_recruitment_analysis(df)
    ret = volunteer_retention_analysis(df)
    wf = workforce_operations(df)
    dem = demand_and_outlook(df)
    cross = finance_recruitment_cross(df)

    top_concern = wf["concerns"].iloc[0]
    top_rec_barrier = rec["rec_barriers"].iloc[0]
    top_ret_barrier = ret["ret_barriers"].iloc[0]
    top_rec_method = rec["rec_methods"].iloc[0]

    reserves_action_count = int(
        wf["actions"]
        .loc[wf["actions"]["label"] == "Unplanned use of reserves", "count"]
        .iloc[0]
    )

    highlights = [
        {
            "rank": 1,
            "title": f"Income is the #1 concern ({top_concern['count']}/{n} organisations)",
            "detail": (
                f"{top_concern['pct']}% of organisations cite income as a top concern, "
                f"with increasing demand being cited as the second most common concern ({wf['concerns'].iloc[1]['pct']}%). "
                "Many are worried about income before their finances have actually deteriorated."
            ),
            "type": "critical",
        },
        {
            "rank": 2,
            "title": "Demand is rising faster than capacity",
            "detail": (
                f"{dem['demand_pct_increased']}% report increased demand, while "
                f"{dem['financial_pct_deteriorated']}% report overall financial position deteriorated (last 3 months). "
                "The gap between income concern and those reporting deteriorated position reflects that many organisations are anxious about funding before deterioration shows in the figures. "
                "Demand is outpacing the resources organisations have to respond with."
            ),
            "type": "critical",
        },
        {
            "rank": 3,
            "title": f"{rec['pct_too_few']}% say they have too few volunteers",
            "detail": (
                f"{rec['pct_difficulty']}% report difficulty actively recruiting volunteers."
            ),
            "type": "warning",
        },
        {
            "rank": 4,
            "title": "Recruitment problem isn't lack of effort",
            "detail": (
                f"The top barrier is '{top_rec_barrier['label']}' "
                f"({top_rec_barrier['count']} organisations); "
                f"{top_rec_method['count']} organisations using {top_rec_method['label'].lower()} to reach people."
            ),
            "type": "warning",
        },
        {
            "rank": 5,
            "title": "Retention barriers are largely external",
            "detail": f"Top retention barrier: '{top_ret_barrier['label']}' ({top_ret_barrier['count']} organisations). Factors outside typical organisational control.",
            "type": "neutral",
        },
        {
            "rank": 6,
            "title": f"{wf['finance_deteriorated_pct']}% report finances deteriorated due to rising costs",
            "detail": (
                f"This is based on the specific 'finances deteriorated from rising costs' question "
                f"(financedeteriorate = 'Yes'). "
                f"{reserves_action_count} "
                f"organisations also report unplanned use of reserves as a response."
            ),
            "type": "critical",
        },
    ]
    if cross:
        diff = abs(
            cross["pct_rec_difficulty_if_finance_deteriorated"]
            - cross["pct_rec_difficulty_if_finance_not_deteriorated"]
        )
        if diff >= 5:
            highlights.append(
                {
                    "rank": 7,
                    "title": "Recruitment difficulty is higher where financial position has deteriorated",
                    "detail": (
                        f"Among organisations whose financial position deteriorated (last 3 months), {cross['pct_rec_difficulty_if_finance_deteriorated']}% "
                        f"find recruitment difficult, compared with {cross['pct_rec_difficulty_if_finance_not_deteriorated']}% "
                        f"among those whose financial position has not deteriorated (n={cross['n_finance_deteriorated']} vs {cross['n_finance_not_deteriorated']})."
                    ),
                    "type": "warning",
                }
            )
    return highlights


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
