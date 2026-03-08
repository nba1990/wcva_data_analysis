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
from src.data_loader import count_multiselect, count_multiselect_by_segment


def _value_counts_ordered(series: pd.Series, order: list[str]) -> pd.DataFrame:
    """Value counts respecting a predefined order, including zeros for missing categories."""
    vc = series.value_counts()
    n = series.notna().sum()
    rows = []
    for val in order:
        count = int(vc.get(val, 0))
        rows.append({"value": val, "count": count, "pct": round(100 * count / n, 1) if n else 0})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 1. Profile summary
# ---------------------------------------------------------------------------

def profile_summary(df: pd.DataFrame) -> dict:
    n = len(df)
    return {
        "n": n,
        "org_size": df["org_size"].value_counts().reindex(ORG_SIZE_ORDER).fillna(0).astype(int).to_dict(),
        "legalform": df["legalform"].value_counts().head(6).to_dict(),
        "wales_scope": df["wales_scope"].value_counts().to_dict(),
        "mainactivity": df["mainactivity"].value_counts().head(10).to_dict(),
        "la_distribution": df["location_la_primary"].value_counts().to_dict(),
        "region_distribution": df["region"].value_counts().to_dict(),
        "social_enterprise_pct": round(100 * (df["socialenterprise"] == "Yes").sum() / n, 1),
        "has_paid_staff_pct": round(100 * (df["paidworkforce"] == "Yes").sum() / n, 1),
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
    return {
        "n": n,
        "shortage_vol_rec": _value_counts_ordered(df["shortage_vol_rec"], YES_NO_ORDER),
        "vol_rec_difficulty": _value_counts_ordered(df["vol_rec"], DIFFICULTY_ORDER),
        "vol_objectives": _value_counts_ordered(df["volobjectives"], VOL_OBJECTIVES_ORDER),
        "rec_methods": count_multiselect(df, REC_METHODS_LABELS),
        "rec_barriers": count_multiselect(df, REC_BARRIERS_LABELS),
        "rec_barriers_by_size": count_multiselect_by_segment(df, REC_BARRIERS_LABELS, "org_size"),
        "rec_methods_by_size": count_multiselect_by_segment(df, REC_METHODS_LABELS, "org_size"),
        "pct_difficulty": round(100 * df["has_vol_rec_difficulty"].sum() / n, 1),
        "pct_too_few": round(
            100 * df["volobjectives"].isin([
                "Slightly too few volunteers", "Significantly too few volunteers"
            ]).sum() / n, 1
        ),
    }


# ---------------------------------------------------------------------------
# 4. Volunteer retention
# ---------------------------------------------------------------------------

def volunteer_retention_analysis(df: pd.DataFrame) -> dict:
    n = len(df)
    return {
        "n": n,
        "shortage_vol_ret": _value_counts_ordered(df["shortage_vol_ret"], YES_NO_ORDER),
        "vol_ret_difficulty": _value_counts_ordered(df["vol_ret"], DIFFICULTY_ORDER),
        "ret_barriers": count_multiselect(df, RET_BARRIERS_LABELS),
        "vol_offer": count_multiselect(df, VOL_OFFER_LABELS),
        "ret_barriers_by_size": count_multiselect_by_segment(df, RET_BARRIERS_LABELS, "org_size"),
        "vol_offer_by_size": count_multiselect_by_segment(df, VOL_OFFER_LABELS, "org_size"),
        "pct_difficulty": round(100 * df["has_vol_ret_difficulty"].sum() / n, 1),
    }


# ---------------------------------------------------------------------------
# 5. Workforce and operations
# ---------------------------------------------------------------------------

def workforce_operations(df: pd.DataFrame) -> dict:
    n = len(df)
    with_staff = df[df["paidworkforce"] == "Yes"]
    n_staff = len(with_staff)

    return {
        "n": n,
        "n_with_staff": n_staff,
        "staff_rec_difficulty": _value_counts_ordered(with_staff["shortage_staff_rec"], YES_NO_ORDER),
        "staff_ret_difficulty": _value_counts_ordered(with_staff["shortage_staff_ret"], YES_NO_ORDER),
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

def cross_segment_analysis(df: pd.DataFrame) -> dict:
    """Key metrics broken down by org_size, scope, and activity."""
    segments = {}

    for seg_col, seg_name in [("org_size", "Organisation Size"), ("wales_scope", "Geographic Scope")]:
        seg_data = {}
        for seg_val in df[seg_col].dropna().unique():
            subset = df[df[seg_col] == seg_val]
            n = len(subset)
            if n < 1:
                continue
            seg_data[seg_val] = {
                "n": n,
                "pct_vol_rec_difficulty": round(100 * subset["has_vol_rec_difficulty"].sum() / n, 1),
                "pct_vol_ret_difficulty": round(100 * subset["has_vol_ret_difficulty"].sum() / n, 1),
                "pct_demand_increased": round(100 * subset["demand_direction"].eq("Increased").sum() / n, 1),
                "pct_finance_deteriorated": round(100 * subset["financial_direction"].eq("Deteriorated").sum() / n, 1),
                "pct_too_few_vols": round(100 * subset["volobjectives"].isin([
                    "Slightly too few volunteers", "Significantly too few volunteers"
                ]).sum() / n, 1),
            }
        segments[seg_name] = seg_data

    return segments


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

    top_concern = wf["concerns"].iloc[0]
    top_rec_barrier = rec["rec_barriers"].iloc[0]
    top_ret_barrier = ret["ret_barriers"].iloc[0]
    top_rec_method = rec["rec_methods"].iloc[0]

    highlights = [
        {
            "rank": 1,
            "title": f"Income is the #1 concern ({top_concern['count']}/{n} organisations)",
            "detail": f"{top_concern['pct']}% of organisations cite income as a top concern, followed by increasing demand ({wf['concerns'].iloc[1]['pct']}%).",
            "type": "critical",
        },
        {
            "rank": 2,
            "title": "Demand is rising faster than capacity",
            "detail": f"{dem['demand_pct_increased']}% report increased demand, yet {dem['financial_pct_deteriorated']}% report worsening finances.",
            "type": "critical",
        },
        {
            "rank": 3,
            "title": f"{rec['pct_too_few']}% say they have too few volunteers",
            "detail": f"{rec['pct_difficulty']}% report active difficulty recruiting volunteers.",
            "type": "warning",
        },
        {
            "rank": 4,
            "title": "Recruitment problem isn't lack of effort",
            "detail": f"The top barrier is '{top_rec_barrier['label']}' ({top_rec_barrier['count']} orgs), despite {top_rec_method['count']} orgs using {top_rec_method['label'].lower()}.",
            "type": "warning",
        },
        {
            "rank": 5,
            "title": "Retention barriers are largely external",
            "detail": f"Top retention barrier: '{top_ret_barrier['label']}' ({top_ret_barrier['count']} orgs). Factors outside typical organisational control.",
            "type": "neutral",
        },
        {
            "rank": 6,
            "title": f"{wf['finance_deteriorated_pct']}% hit by rising costs",
            "detail": f"{wf['actions'].query('label == \"Unplanned use of reserves\"')['count'].values[0]} organisations made unplanned use of reserves.",
            "type": "critical",
        },
    ]
    return highlights
