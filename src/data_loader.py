"""
Data loading, cleaning, and derived-column creation for the Baromedr Cymru Wave 2
anonymised dataset.

This module provides:
- load_dataset: Load main survey CSV, clean and add derived columns.
- load_la_context: Load local-authority context (cached).
- count_multiselect and count_multiselect_by_segment: Aggregate multi-select responses.
- data_quality_profile: Summary for the Data Notes page.

All functions expect or return pandas DataFrames with column names aligned to
config label dictionaries (CONCERNS_LABELS, ACTIONS_LABELS, etc.).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import DATA_DIR, DATASET_PATH, LA_TO_REGION, MULTI_SELECT_GROUPS


def load_dataset(path: str | None = None) -> pd.DataFrame:
    """Load the main survey CSV and apply cleaning and derivation.

    Args:
        path: Optional path to CSV. If None, uses config DATASET_PATH.

    Returns:
        DataFrame with original questionnaire columns plus derived columns
        (region, demand_direction, financial_direction, has_X_difficulty flags,
        finance_deteriorated, and per-group X_count for multi-select groups).
    """
    df = pd.read_csv(path or DATASET_PATH)
    df = _clean(df)
    df = _derive_columns(df)
    return df


@lru_cache(maxsize=2)
def load_la_context(path: str | None = None) -> pd.DataFrame:
    """Load local-authority context (population, estimated VCSE org counts).

    The CSV is small and static; cached per process to avoid repeated disk reads.
    Column 'local_authority' is stripped of leading/trailing whitespace.

    Args:
        path: Optional path to CSV. If None, uses DATA_DIR / "la_context_wales.csv".

    Returns:
        DataFrame with at least 'local_authority' and context columns for joining.
    """
    csv_path = Path(path) if path is not None else DATA_DIR / "la_context_wales.csv"
    ctx = pd.read_csv(csv_path)
    ctx["local_authority"] = ctx["local_authority"].str.strip()
    return ctx


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise string columns and coerce numeric columns.

    - Object columns: strip whitespace; empty string becomes NaN.
    - peopleemploy, peoplevol, monthsreserves: coerced to numeric (invalid → NaN).

    Args:
        df: Raw DataFrame from read_csv.

    Returns:
        DataFrame in place with cleaned columns (may mutate input).
    """
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
    """Add derived analytical columns for EDA and filtering.

    New columns: region (from LA), demand_direction, financial_direction,
    has_vol_rec_difficulty, has_vol_ret_difficulty, has_staff_rec_difficulty,
    has_staff_ret_difficulty, finance_deteriorated, and for each key in
    MULTI_SELECT_GROUPS a {key}_count series (number of selected options per row).

    Args:
        df: DataFrame with at least location_la_primary, demand, financial,
            shortage_*, financedeteriorate, and any multi-select columns.

    Returns:
        New DataFrame with original + derived columns (concat on axis=1).
    """
    demand_map = {
        "Increased a lot": "Increased",
        "Increased a little": "Increased",
        "Stayed the same": "Stayed the same",
        "Decreased a little": "Decreased",
        "Decreased a lot": "Decreased",
        "Don't know": "Don't know",
    }
    financial_map = {
        "Improved a lot": "Improved",
        "Improved a little": "Improved",
        "Stayed the same": "Stayed the same",
        "Deteriorated a little": "Deteriorated",
        "Deteriorated a lot": "Deteriorated",
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

    Only columns present in both df and label_dict are used. Percentages are
    over len(df). Empty result returns a DataFrame with columns column, label,
    count, pct (no rows).

    Args:
        df: Survey DataFrame; may contain a subset of label_dict keys.
        label_dict: Mapping from column name to display label (e.g. CONCERNS_LABELS).

    Returns:
        DataFrame with columns ['column', 'label', 'count', 'pct'], sorted by
        count descending.
    """
    cols = [c for c in label_dict if c in df.columns]
    n = len(df)
    rows = []
    for col in cols:
        count = df[col].notna().sum()
        rows.append(
            {
                "column": col,
                "label": label_dict[col],
                "count": int(count),
                "pct": round(100 * count / n, 1) if n else 0,
            }
        )

    if not rows:
        # Return an empty but well-formed frame so downstream code that expects
        # 'label' / 'count' / 'pct' columns continues to work.
        return pd.DataFrame(columns=["column", "label", "count", "pct"])

    result = (
        pd.DataFrame(rows).sort_values("count", ascending=False).reset_index(drop=True)
    )
    return result


def count_multiselect_by_segment(
    df: pd.DataFrame,
    label_dict: dict[str, str],
    segment_col: str,
) -> pd.DataFrame:
    """Count multi-select responses as percentages within each segment.

    For each label (from label_dict) and each segment value, computes the
    percentage of rows in that segment with a non-null value for the
    corresponding column. Segment with zero rows yields 0.0.

    Args:
        df: Survey DataFrame; must contain segment_col and columns in label_dict.
        label_dict: Mapping from column name to display label.
        segment_col: Categorical column to segment by (e.g. 'org_size').

    Returns:
        DataFrame with columns ['label'] plus one column per segment value,
        each value a float percentage (0–100).
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


def data_quality_profile(df: pd.DataFrame) -> dict[str, Any]:
    """Build a data quality summary for the Data Notes page.

    Includes row/column counts, missing counts and percentages per column,
    org_size/location_la_primary missing counts, complete-row count and percentage,
    and block_completeness (percentage of answered questions per question block).

    Args:
        df: Survey DataFrame; expects columns org_size, location_la_primary and
            optionally question_blocks columns.

    Returns:
        Dict with keys: n_rows, n_cols, missing_by_col, missing_pct_by_col,
        org_size_missing, la_missing, complete_rows, complete_pct,
        block_completeness (dict block_name -> pct).
    """
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
            "legalform",
            "mainactivity",
            "socialenterprise",
            "paidworkforce",
            "org_size",
            "location_la_primary",
            "wales_scope",
        ],
        "Experience (last 3 months)": [
            "demand",
            "workforce",
            "volunteers",
            "financial",
        ],
        "Expectations (next 3 months)": [
            "expectdemand",
            "expectworkforce",
            "expectvolunteers",
            "expectfinancial",
            "op_demand",
        ],
        "Operational Challenges": [
            "shortage_staff_rec",
            "shortage_staff_ret",
            "shortage_vol_rec",
            "shortage_vol_ret",
            "operating",
        ],
        "Finances": [
            "financedeteriorate",
            "reserves",
            "usingreserves",
            "monthsreserves",
        ],
        "Volunteering (recruitment)": [
            "volobjectives",
            "vol_manager",
            "vol_rec",
        ],
        "Volunteering (retention)": [
            "vol_ret",
            "vol_time",
        ],
        "Earned Settlement": [
            "earnedsettlement",
            "settlement_capacity",
        ],
    }

    block_completeness = {}
    for block_name, block_cols in question_blocks.items():
        existing = [c for c in block_cols if c in df.columns]
        if existing:
            answered = df[existing].notna().sum().sum()
            possible = n * len(existing)
            block_completeness[block_name] = (
                round(100 * answered / possible, 1) if possible else 0
            )

    profile["block_completeness"] = block_completeness
    return profile
