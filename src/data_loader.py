# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
Data loading, cleaning, and derived-column creation for the Baromedr Cymru Wave 2
anonymised dataset.

This module provides:
- load_dataset: Load main survey CSV, clean and add derived columns.
- load_la_context: Load local-authority context (cached).
- check_runtime_assets: Verify required and optional runtime files for deployment.
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

from src.config import (
    LA_TO_REGION,
    MULTI_SELECT_GROUPS,
    PROJECT_ROOT,
    WCVA_LOGGER,
    RuntimeDataSource,
    mask_runtime_value,
    resolve_dataset_source,
    resolve_la_context_source,
)


def _read_csv_from_source(source: RuntimeDataSource) -> pd.DataFrame:
    """Read a CSV from a resolved runtime source."""
    if source.is_url:
        try:
            WCVA_LOGGER.info(
                "Reading dataset from URL",
                extra={
                    "source_type": source.source_type,
                    "url": mask_runtime_value(source.value),
                },
            )
            df = pd.read_csv(source.value)
            WCVA_LOGGER.info(
                "Loaded dataset from URL",
                extra={
                    "source_type": source.source_type,
                    "url": mask_runtime_value(source.value),
                    "n_rows": int(len(df)),
                    "n_cols": int(len(df.columns)),
                },
            )
            return df
        except Exception as exc:
            WCVA_LOGGER.error(
                "Failed to read CSV from URL",
                extra={
                    "source_type": source.source_type,
                    "url": mask_runtime_value(source.value),
                },
            )
            raise RuntimeError(
                f"Failed to read CSV from {mask_runtime_value(source.value)}."
            ) from exc
    path = Path(source.value)
    WCVA_LOGGER.info(
        "Reading dataset from file",
        extra={"source_type": source.source_type, "path": str(path)},
    )
    df = pd.read_csv(path)
    WCVA_LOGGER.info(
        "Loaded dataset from file",
        extra={
            "source_type": source.source_type,
            "path": str(path),
            "n_rows": int(len(df)),
            "n_cols": int(len(df.columns)),
        },
    )
    return df


def load_dataset(
    path: str | None = None,
    *,
    return_source: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, RuntimeDataSource]:
    """Load the main survey CSV and apply cleaning and derivation.

    Args:
        path: Optional path to CSV. If None, resolves the configured runtime
            file path or URL.
        return_source: If True, also return the resolved runtime source metadata.

    Returns:
        DataFrame with original questionnaire columns plus derived columns
        (region, demand_direction, financial_direction, has_X_difficulty flags,
        finance_deteriorated, and per-group X_count for multi-select groups).
        When ``return_source`` is True, returns ``(df, source)``.
    """
    source = (
        RuntimeDataSource(
            label="Wave dataset",
            value=str(Path(path)),
            source_type="default_path",
            exists=Path(path).exists(),
            is_url=False,
            attempted=(f"explicit_path -> {path}",),
        )
        if path is not None
        else resolve_dataset_source()
    )

    if source.exists:
        WCVA_LOGGER.info(
            "Resolved Wave dataset source",
            extra={
                "label": source.label,
                "value": mask_runtime_value(source.value),
                "source_type": source.source_type,
                "is_url": source.is_url,
                "is_demo": source.is_demo,
            },
        )
        df = _read_csv_from_source(source)
    else:
        WCVA_LOGGER.error(
            "Wave dataset not found",
            extra={
                "label": source.label,
                "value": mask_runtime_value(source.value),
                "source_type": source.source_type,
                "is_url": source.is_url,
                "is_demo": source.is_demo,
            },
        )
        raise FileNotFoundError(
            "Wave 2 dataset not found. Set WCVA_DATASET_PATH or WCVA_DATASET_URL, "
            "configure dataset_path / dataset_url in Streamlit secrets, or place "
            "an untracked local copy at datasets/WCVA_W2_Anonymised_Dataset.csv."
        )

    df = _clean(df)
    df = _derive_columns(df)
    if return_source:
        return df, source
    return df


def check_runtime_assets(
    project_root: str | Path | None = None,
    dataset_path: str | Path | None = None,
    dataset_url: str | None = None,
    la_context_path: str | Path | None = None,
    la_context_url: str | None = None,
) -> dict[str, Any]:
    """Check that required and optional runtime assets exist for deployment.

    Args:
        project_root: Optional project root override, mainly for tests.
        dataset_path: Optional dataset CSV override; defaults to configured runtime path.
        dataset_url: Optional dataset CSV URL override.
        la_context_path: Optional local-authority context CSV override.
        la_context_url: Optional local-authority context CSV URL override.

    Returns:
        Dict with asset rows and summary flags for deployment health checks.
    """
    root = Path(project_root) if project_root is not None else PROJECT_ROOT
    dataset_source = (
        RuntimeDataSource(
            label="Wave dataset",
            value=dataset_url or str(Path(dataset_path)),
            source_type="env_url" if dataset_url else "env_path",
            exists=True if dataset_url else Path(dataset_path).exists(),
            is_url=bool(dataset_url),
            attempted=(
                (
                    f"explicit_url -> {mask_runtime_value(dataset_url)}"
                    if dataset_url
                    else f"explicit_path -> {dataset_path}"
                ),
            ),
        )
        if dataset_path is not None or dataset_url is not None
        else resolve_dataset_source()
    )
    la_context_source = (
        RuntimeDataSource(
            label="Local-authority context",
            value=la_context_url or str(Path(la_context_path)),
            source_type="env_url" if la_context_url else "env_path",
            exists=True if la_context_url else Path(la_context_path).exists(),
            is_url=bool(la_context_url),
            attempted=(
                (
                    f"explicit_url -> {mask_runtime_value(la_context_url)}"
                    if la_context_url
                    else f"explicit_path -> {la_context_path}"
                ),
            ),
        )
        if la_context_path is not None or la_context_url is not None
        else resolve_la_context_source()
    )
    streamlit_config = root / ".streamlit/config.toml"
    sroi_mindmap = (
        root
        / "references/SROI_Wales_Voluntary_Sector/docs/WCVA_Text_Interactive_MindMap.html"
    )
    sroi_briefing_pdf = (
        root
        / "references/SROI_Wales_Voluntary_Sector/docs/SROI_Wales_Voluntary_Sector.pdf"
    )

    WCVA_LOGGER.info(
        "Runtime asset check",
        extra={
            "dataset_source": {
                "value": mask_runtime_value(dataset_source.value),
                "source_type": dataset_source.source_type,
                "is_url": dataset_source.is_url,
                "is_demo": dataset_source.is_demo,
                "exists": dataset_source.exists,
            },
            "la_context_source": {
                "value": mask_runtime_value(la_context_source.value),
                "source_type": la_context_source.source_type,
                "is_url": la_context_source.is_url,
                "exists": la_context_source.exists,
            },
        },
    )

    required_assets = [
        {
            "label": "Wave 2 dataset source",
            "path": mask_runtime_value(dataset_source.value),
            "exists": dataset_source.exists,
            "kind": "required",
            "source_type": dataset_source.source_type,
            "mode": "demo" if dataset_source.is_demo else "real",
        },
        {
            "label": "Streamlit config",
            "path": str(streamlit_config),
            "exists": streamlit_config.exists(),
            "kind": "required",
        },
    ]

    optional_assets = [
        {
            "label": "Local authority context CSV",
            "path": mask_runtime_value(la_context_source.value),
            "exists": la_context_source.exists,
            "kind": "optional",
            "source_type": la_context_source.source_type,
        },
        {
            "label": "SROI mind-map HTML",
            "path": str(sroi_mindmap),
            "exists": sroi_mindmap.exists(),
            "kind": "optional",
        },
        {
            "label": "SROI briefing PDF",
            "path": str(sroi_briefing_pdf),
            "exists": sroi_briefing_pdf.exists(),
            "kind": "optional",
        },
    ]

    missing_required = [row["label"] for row in required_assets if not row["exists"]]
    missing_optional = [row["label"] for row in optional_assets if not row["exists"]]

    return {
        "required": required_assets,
        "optional": optional_assets,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "all_required_present": not missing_required,
        "app_mode": "demo" if dataset_source.is_demo else "real",
        "dataset_source": dataset_source,
        "la_context_source": la_context_source,
    }


@lru_cache(maxsize=2)
def load_la_context(
    path: str | None = None,
    *,
    return_source: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, RuntimeDataSource]:
    """Load local-authority context (population, estimated VCSE org counts).

    The CSV is small and static; cached per process to avoid repeated disk reads.
    Column 'local_authority' is stripped of leading/trailing whitespace.

    Args:
        path: Optional path to CSV. If None, uses the configured runtime path.
        return_source: If True, also return the resolved runtime source metadata.

    Returns:
        DataFrame with at least 'local_authority' and context columns for joining.
        When ``return_source`` is True, returns ``(ctx, source)``.
    """
    source = (
        RuntimeDataSource(
            label="Local-authority context",
            value=str(Path(path)),
            source_type="default_path",
            exists=Path(path).exists(),
            is_url=False,
            attempted=(f"explicit_path -> {path}",),
        )
        if path is not None
        else resolve_la_context_source()
    )

    if source.exists:
        ctx = _read_csv_from_source(source)
    else:
        raise FileNotFoundError(
            "Local-authority context not found. Set WCVA_LA_CONTEXT_PATH or "
            "WCVA_LA_CONTEXT_URL, or configure la_context_path / la_context_url "
            "in Streamlit secrets."
        )

    ctx["local_authority"] = ctx["local_authority"].str.strip()
    if return_source:
        return ctx, source
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


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
