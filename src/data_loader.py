"""
Data loading, cleaning, and derived-column creation for the
Baromedr Cymru Wave 2 anonymised dataset.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from src.config import DATASET_PATH, LA_TO_REGION, MULTI_SELECT_GROUPS


def load_dataset(path: str | None = None) -> pd.DataFrame:
    """Load the CSV and apply all cleaning / derivation steps."""
    df = pd.read_csv(path or DATASET_PATH)
    df = _clean(df)
    df = _derive_columns(df)
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning: strip whitespace, normalise blanks."""
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip().replace("", np.nan)

    if "peopleemploy" in df.columns:
        df["peopleemploy"] = pd.to_numeric(df["peopleemploy"], errors="coerce")
    if "peoplevol" in df.columns:
        df["peoplevol"] = pd.to_numeric(df["peoplevol"], errors="coerce")
    if "monthsreserves" in df.columns:
        df["monthsreserves"] = pd.to_numeric(df["monthsreserves"], errors="coerce")

    return df


def _derive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived analytical columns."""
    demand_map = {
        "Increased a lot": "Increased", "Increased a little": "Increased",
        "Stayed the same": "Stayed the same",
        "Decreased a little": "Decreased", "Decreased a lot": "Decreased",
        "Don't know": "Don't know",
    }
    financial_map = {
        "Improved a lot": "Improved", "Improved a little": "Improved",
        "Stayed the same": "Stayed the same",
        "Deteriorated a little": "Deteriorated", "Deteriorated a lot": "Deteriorated",
        "Don't know": "Don't know",
    }

    new_cols = {
        "region": df["location_la_primary"].map(LA_TO_REGION),
        "demand_direction": df["demand"].map(demand_map),
        "financial_direction": df["financial"].map(financial_map),
        "has_vol_rec_difficulty": df["shortage_vol_rec"] == "Yes",
        "has_vol_ret_difficulty": df["shortage_vol_ret"] == "Yes",
        "has_staff_rec_difficulty": df["shortage_staff_rec"] == "Yes",
        "has_staff_ret_difficulty": df["shortage_staff_ret"] == "Yes",
        "finance_deteriorated": df["financedeteriorate"] == "Yes",
    }

    for group_name, label_dict in MULTI_SELECT_GROUPS.items():
        existing = [c for c in label_dict if c in df.columns]
        new_cols[f"{group_name}_count"] = df[existing].notna().sum(axis=1)

    return pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)


def count_multiselect(df: pd.DataFrame, label_dict: dict[str, str]) -> pd.DataFrame:
    """Count non-null responses for a group of wide-format multi-select columns.

    Returns a DataFrame with columns ['label', 'count', 'pct'] sorted descending.
    """
    cols = [c for c in label_dict if c in df.columns]
    n = len(df)
    rows = []
    for col in cols:
        count = df[col].notna().sum()
        rows.append({
            "column": col,
            "label": label_dict[col],
            "count": int(count),
            "pct": round(100 * count / n, 1) if n else 0,
        })
    result = pd.DataFrame(rows).sort_values("count", ascending=False).reset_index(drop=True)
    return result


def count_multiselect_by_segment(
    df: pd.DataFrame,
    label_dict: dict[str, str],
    segment_col: str,
) -> pd.DataFrame:
    """Count multi-select responses segmented by a categorical column.

    Returns a DataFrame with ['label', segment_value_1, segment_value_2, ...].
    """
    segments = df[segment_col].dropna().unique()
    cols = [c for c in label_dict if c in df.columns]
    rows = []
    for col in cols:
        row = {"label": label_dict[col]}
        for seg in sorted(segments):
            subset = df[df[segment_col] == seg]
            n_seg = len(subset)
            count = subset[col].notna().sum()
            row[seg] = round(100 * count / n_seg, 1) if n_seg else 0
        rows.append(row)
    return pd.DataFrame(rows)


def data_quality_profile(df: pd.DataFrame) -> dict:
    """Return a data quality summary for the Data Notes page."""
    n = len(df)
    profile = {
        "n_rows": n,
        "n_cols": len(df.columns),
        "missing_by_col": df.isnull().sum().to_dict(),
        "missing_pct_by_col": (df.isnull().sum() / n * 100).round(1).to_dict(),
        "org_size_missing": int(df["org_size"].isna().sum()),
        "la_missing": int(df["location_la_primary"].isna().sum()),
        "complete_rows": int((~df.isnull().any(axis=1)).sum()),
        "complete_pct": round(100 * (~df.isnull().any(axis=1)).sum() / n, 1),
    }

    question_blocks = {
        "Organisational Profile": [
            "legalform", "mainactivity", "socialenterprise", "paidworkforce",
            "org_size", "location_la_primary", "wales_scope",
        ],
        "Experience (last 3 months)": [
            "demand", "workforce", "volunteers", "financial",
        ],
        "Expectations (next 3 months)": [
            "expectdemand", "expectworkforce", "expectvolunteers", "expectfinancial", "op_demand",
        ],
        "Operational Challenges": [
            "shortage_staff_rec", "shortage_staff_ret", "shortage_vol_rec", "shortage_vol_ret",
            "operating",
        ],
        "Finances": [
            "financedeteriorate", "reserves", "usingreserves", "monthsreserves",
        ],
        "Volunteering (recruitment)": [
            "volobjectives", "vol_manager", "vol_rec",
        ],
        "Volunteering (retention)": [
            "vol_ret", "vol_time",
        ],
        "Earned Settlement": [
            "earnedsettlement", "settlement_capacity",
        ],
    }

    block_completeness = {}
    for block_name, block_cols in question_blocks.items():
        existing = [c for c in block_cols if c in df.columns]
        if existing:
            answered = df[existing].notna().sum().sum()
            possible = n * len(existing)
            block_completeness[block_name] = round(100 * answered / possible, 1) if possible else 0

    profile["block_completeness"] = block_completeness
    return profile
