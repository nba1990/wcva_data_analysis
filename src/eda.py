"""
Exploratory data analysis functions for Baromedr Cymru Wave 2.

Each function takes a (possibly filtered) DataFrame and returns
structured results ready for charting or display.
"""

from __future__ import annotations

import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    CONCERNS_LABELS, ACTIONS_LABELS, SHORTAGE_AFFECT_LABELS,
    REC_METHODS_LABELS, REC_BARRIERS_LABELS, RET_BARRIERS_LABELS,
    VOL_OFFER_LABELS, VOL_DEM_LABELS, VOL_DEM_CHANGE_LABELS,
    VOL_TYPEUSE_LABELS, DEMAND_ORDER, FINANCIAL_ORDER, DIFFICULTY_ORDER,
    OPERATING_ORDER, VOL_OBJECTIVES_ORDER, VOL_TYPEUSE_ORDER,
    EARNED_SETTLEMENT_ORDER, ORG_SIZE_ORDER, YES_NO_ORDER,
    EXPECT_DEMAND_ORDER, EXPECT_FINANCIAL_ORDER,
)
from src.data_loader import count_multiselect, count_multiselect_by_segment, load_la_context


def _value_counts_ordered(series: pd.Series, order: list[str]) -> pd.DataFrame:
    """Value counts respecting a predefined order, including zeros for missing categories."""
    vc = series.value_counts()
    n = series.notna().sum()
    rows = []
    for val in order:
        count = int(vc.get(val, 0))
        rows.append({"value": val, "count": count, "pct": round(100 * count / n, 1) if n else 0})
    return pd.DataFrame(rows)


def _share_true(series: pd.Series) -> float:
    """
    Return percentage of 'True' values using a non-missing base.

    Design convention:
    - For any single survey question, percentages are calculated over respondents
      with a non-missing answer to that question (series.notna()).
    - This keeps figures consistent between KPI tiles, charts, and narratives,
      and avoids discrepancies when some organisations skip a question.
    """
    base = int(series.notna().sum())
    if base == 0:
        return 0.0
    return round(100 * series.sum() / base, 1)


# ---------------------------------------------------------------------------
# 1. Profile summary
# ---------------------------------------------------------------------------

def profile_summary(df: pd.DataFrame) -> dict:
    n = len(df)

    # Basic distributions used throughout the app
    org_size = df["org_size"].value_counts().reindex(ORG_SIZE_ORDER).fillna(0).astype(int).to_dict()
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
    la_merged["sample_per_100k"] = la_merged["sample_count"] / la_merged["population_2024"] * 100000.0
    la_merged["orgs_per_10k_pop"] = la_merged["est_vcse_orgs"] / la_merged["population_2024"] * 10000.0
    # Over/under-representation index (100 = proportional to population)
    la_merged["representation_index"] = (
        la_merged["sample_share_pct"] / la_merged["pop_share_pct"]
    ).replace([pd.NA, pd.NaT], 0.0)

    # Share of organisations reporting any volunteers.
    # We treat strictly positive volunteer counts as having volunteers.
    has_volunteers_pct = round(
        100
        * (df["peoplevol"].fillna(0) > 0).sum()
        / n,
        1,
    ) if n else 0

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
        "social_enterprise_pct": round(100 * (df["socialenterprise"] == "Yes").sum() / n, 1),
        "has_paid_staff_pct": round(100 * (df["paidworkforce"] == "Yes").sum() / n, 1),
        "has_volunteers_pct": has_volunteers_pct,
        "median_employees": df["peopleemploy"].median(),
        "median_volunteers": df["peoplevol"].median(),
    }


# ---------------------------------------------------------------------------
# 2. Demand and outlook
# ---------------------------------------------------------------------------

def demand_and_outlook(df: pd.DataFrame) -> dict:
    return {
        "demand": _value_counts_ordered(df["demand"], DEMAND_ORDER),
        "financial": _value_counts_ordered(df["financial"], FINANCIAL_ORDER),
        "operating": _value_counts_ordered(df["operating"], OPERATING_ORDER),
        "workforce_change": _value_counts_ordered(df["workforce"], DEMAND_ORDER),
        "expect_demand": _value_counts_ordered(df["expectdemand"], EXPECT_DEMAND_ORDER),
        "expect_financial": _value_counts_ordered(df["expectfinancial"], EXPECT_FINANCIAL_ORDER),
        "demand_pct_increased": round(100 * df["demand_direction"].eq("Increased").sum() / len(df), 1),
        "financial_pct_deteriorated": round(
            100 * df["financial_direction"].eq("Deteriorated").sum() / len(df), 1
        ),
        "operating_pct_likely": round(
            100 * df["operating"].isin(["Very likely", "Quite likely"]).sum() / len(df), 1
        ),
    }


# ---------------------------------------------------------------------------
# 3. Volunteer recruitment
# ---------------------------------------------------------------------------

def volunteer_recruitment_analysis(df: pd.DataFrame) -> dict:
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
        "vol_objectives": _value_counts_ordered(df["volobjectives"], VOL_OBJECTIVES_ORDER),
        "rec_methods": count_multiselect(df, REC_METHODS_LABELS),
        "rec_barriers": count_multiselect(df, REC_BARRIERS_LABELS),
        "rec_barriers_by_size": count_multiselect_by_segment(df, REC_BARRIERS_LABELS, "org_size"),
        "rec_methods_by_size": count_multiselect_by_segment(df, REC_METHODS_LABELS, "org_size"),
        # Share finding recruitment somewhat or extremely difficult (Likert-based, non-missing base)
        "difficulty_base": likert_base,
        "pct_difficulty": round(100 * likert_hard / likert_base, 1) if likert_base else 0,
        # Share explicitly reporting a shortage recruiting volunteers (non-missing base)
        "pct_shortage": _share_true(shortage_series),
        "pct_too_few": (
            lambda series: (
                round(
                    100
                    * series.isin(
                        ["Slightly too few volunteers", "Significantly too few volunteers"]
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

def volunteer_retention_analysis(df: pd.DataFrame) -> dict:
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
        "ret_barriers_by_size": count_multiselect_by_segment(df, RET_BARRIERS_LABELS, "org_size"),
        "vol_offer_by_size": count_multiselect_by_segment(df, VOL_OFFER_LABELS, "org_size"),
        # Share finding retention somewhat or extremely difficult (Likert-based, non-missing base)
        "difficulty_base": likert_base,
        "pct_difficulty": round(100 * likert_hard / likert_base, 1) if likert_base else 0,
        # Share explicitly reporting a shortage retaining volunteers (non-missing base)
        "pct_shortage": _share_true(shortage_series),
    }


# ---------------------------------------------------------------------------
# 5. Workforce and operations
# ---------------------------------------------------------------------------

def workforce_operations(df: pd.DataFrame) -> dict:
    n = len(df)
    with_staff = df[df["paidworkforce"] == "Yes"]
    n_staff = len(with_staff)

    staff_rec_difficulty = _value_counts_ordered(with_staff["shortage_staff_rec"], YES_NO_ORDER)
    staff_ret_difficulty = _value_counts_ordered(with_staff["shortage_staff_ret"], YES_NO_ORDER)

    # Among organisations with paid staff, share reporting recruitment/retention difficulties.
    if n_staff:
        rec_yes_row = staff_rec_difficulty[staff_rec_difficulty["value"] == "Yes"]
        ret_yes_row = staff_ret_difficulty[staff_ret_difficulty["value"] == "Yes"]
        staff_rec_difficulty_pct = float(rec_yes_row["pct"].iloc[0]) if not rec_yes_row.empty else 0.0
        staff_ret_difficulty_pct = float(ret_yes_row["pct"].iloc[0]) if not ret_yes_row.empty else 0.0
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
        "finance_deteriorated_pct": round(100 * df["finance_deteriorated"].sum() / n, 1),
        "reserves_yes_pct": round(100 * (df["reserves"] == "Yes").sum() / n, 1),
        "using_reserves_pct": round(
            100 * (df["usingreserves"] == "Yes").sum() / df["reserves"].eq("Yes").sum(), 1
        ) if df["reserves"].eq("Yes").sum() > 0 else 0,
        "median_months_reserves": df["monthsreserves"].median(),
        "workforce_change": _value_counts_ordered(df["workforce"], DEMAND_ORDER),
    }


# ---------------------------------------------------------------------------
# 6. Volunteer demographics
# ---------------------------------------------------------------------------

def volunteer_demographics(df: pd.DataFrame) -> dict:
    dem_presence = count_multiselect(df, VOL_DEM_LABELS)

    # Build a change matrix: rows = demographic group, cols = change category
    change_order = [
        "Increased a lot", "Increased a little", "Stayed the same",
        "Decreased a little", "Decreased a lot", "Not applicable",
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
            ["Increased a lot", "Increased a little", "Stayed the same",
             "Decreased a little", "Decreased a lot", "Don't know"],
        ),
    }


# ---------------------------------------------------------------------------
# 7. Volunteering types and earned settlement
# ---------------------------------------------------------------------------

def volunteering_types(df: pd.DataFrame) -> dict:
    type_data = {}
    for col, label in VOL_TYPEUSE_LABELS.items():
        if col in df.columns:
            type_data[label] = _value_counts_ordered(df[col], VOL_TYPEUSE_ORDER)

    return {
        "n": len(df),
        "type_data": type_data,
        "earned_settlement": _value_counts_ordered(df["earnedsettlement"], EARNED_SETTLEMENT_ORDER),
        "settlement_capacity": df["settlement_capacity"].value_counts().to_dict(),
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
        "pct_finance_deteriorated": _share_true(subset["financial_direction"].eq("Deteriorated")),
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


def cross_segment_analysis(df: pd.DataFrame) -> dict:
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


def finance_recruitment_cross(df: pd.DataFrame) -> dict | None:
    """
    Among orgs whose finances deteriorated vs not, what % find recruitment difficult?
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
    pct_not_det = round(100 * rec_hard[not_det_answered].sum() / max(1, not_det_answered.sum()), 1)
    return {
        "pct_rec_difficulty_if_finance_deteriorated": pct_det,
        "pct_rec_difficulty_if_finance_not_deteriorated": pct_not_det,
        "n_finance_deteriorated": int(n_det),
        "n_finance_not_deteriorated": int(n_not_det),
    }


# ---------------------------------------------------------------------------
# 9. Executive summary highlights
# ---------------------------------------------------------------------------

def executive_highlights(df: pd.DataFrame) -> list[dict]:
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
                f"{dem['financial_pct_deteriorated']}% already report worsening finances. "
                "The gap between income concern and those reporting worsening finances reflects that many organisations are anxious about funding before deterioration shows in the figures. "
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
            "title": f"{wf['finance_deteriorated_pct']}% hit by rising costs",
            "detail": f"{wf['actions'].query('label == \"Unplanned use of reserves\"')['count'].values[0]} organisations made unplanned use of reserves.",
            "type": "critical",
        },
    ]
    if cross:
        diff = abs(
            cross["pct_rec_difficulty_if_finance_deteriorated"]
            - cross["pct_rec_difficulty_if_finance_not_deteriorated"]
        )
        if diff >= 5:
            highlights.append({
                "rank": 7,
                "title": "Recruitment difficulty is higher where finances have deteriorated",
                "detail": (
                    f"Among organisations reporting deteriorating finances, {cross['pct_rec_difficulty_if_finance_deteriorated']}% "
                    f"find recruitment difficult, compared with {cross['pct_rec_difficulty_if_finance_not_deteriorated']}% "
                    f"among those whose finances have not deteriorated (n={cross['n_finance_deteriorated']} vs {cross['n_finance_not_deteriorated']})."
                ),
                "type": "warning",
            })
    return highlights
