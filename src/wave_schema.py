from __future__ import annotations

"""
Schema and mapping layer for per-wave configurations.

This module is intentionally small and focused on:

- loading a YAML schema for a given wave; and
- evaluating a minimal set of metric definitions (share_eq, share_in,
  share_gt, conditional_share) against a DataFrame.

It does not attempt to be a generic transformation engine; complex logic
should remain in src.eda or specialised helpers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml

from src.config import PROJECT_ROOT

MetricType = Literal["share_eq", "share_in", "share_gt", "conditional_share"]


@dataclass(frozen=True)
class MetricDefinition:
    """Definition of how to compute a single canonical metric for a wave."""

    id: str
    type: MetricType
    config: dict[str, Any]


@dataclass(frozen=True)
class WaveSchema:
    """Loaded per-wave schema with metadata and metric definitions."""

    wave_label: str
    wave_number: int
    metrics: dict[str, MetricDefinition]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Wave schema at {path} must be a mapping.")
    return data


def load_wave_schema(wave_id: str) -> WaveSchema:
    """
    Load the schema for a given wave (e.g. 'wave2').

    For now this is a thin wrapper over YAML; if future waves need stricter
    validation we can migrate these definitions to a Pydantic model.
    """
    schema_path = PROJECT_ROOT / "config" / "waves" / f"{wave_id}.schema.yml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Wave schema not found at {schema_path}")

    raw = _load_yaml(schema_path)

    meta = raw.get("meta") or {}
    wave_label = str(meta.get("wave_label") or wave_id)
    wave_number = int(meta.get("wave_number") or 0)

    metrics_raw = raw.get("metrics") or {}
    metrics: dict[str, MetricDefinition] = {}
    for metric_id, cfg in metrics_raw.items():
        if not isinstance(cfg, dict):
            continue
        mtype_raw = cfg.get("type")
        if mtype_raw == "share_eq":
            mtype: MetricType = "share_eq"
        elif mtype_raw == "share_in":
            mtype = "share_in"
        elif mtype_raw == "share_gt":
            mtype = "share_gt"
        elif mtype_raw == "conditional_share":
            mtype = "conditional_share"
        else:
            # Unknown or disabled metric: skip rather than failing schema load.
            continue
        metrics[metric_id] = MetricDefinition(id=metric_id, type=mtype, config=cfg)

    return WaveSchema(wave_label=wave_label, wave_number=wave_number, metrics=metrics)


def _series_non_missing(series: pd.Series) -> pd.Series:
    """Return series filtered to non-missing values, for consistent bases."""
    return series[series.notna()]


def evaluate_share_eq(df: pd.DataFrame, column: str, value: Any) -> int:
    """Percentage (0–100) where df[column] == value over non-missing base."""
    if column not in df.columns:
        return 0
    series = _series_non_missing(df[column])
    base = len(series)
    if base == 0:
        return 0
    count = int((series == value).sum())
    return int(round(100 * count / base))


def evaluate_share_in(df: pd.DataFrame, column: str, values: list[Any]) -> int:
    """Percentage (0–100) where df[column] is in values over non-missing base."""
    if column not in df.columns:
        return 0
    series = _series_non_missing(df[column])
    base = len(series)
    if base == 0:
        return 0
    count = int(series.isin(values).sum())
    return int(round(100 * count / base))


def evaluate_share_gt(df: pd.DataFrame, column: str, threshold: float) -> int:
    """Percentage (0–100) where df[column] > threshold over non-missing base."""
    if column not in df.columns:
        return 0
    series = pd.to_numeric(df[column], errors="coerce")
    series = _series_non_missing(series)
    base = len(series)
    if base == 0:
        return 0
    count = int((series > threshold).sum())
    return int(round(100 * count / base))


def evaluate_conditional_share(
    df: pd.DataFrame,
    *,
    condition_column: str,
    condition_value: Any,
    numerator_column: str,
    numerator_value: Any,
) -> int:
    """
    Percentage (0–100) where numerator_column == numerator_value among rows
    where condition_column == condition_value.
    """
    if condition_column not in df.columns or numerator_column not in df.columns:
        return 0
    cond = df[condition_column] == condition_value
    subset = df[cond]
    if subset.empty:
        return 0
    series = _series_non_missing(subset[numerator_column])
    base = len(series)
    if base == 0:
        return 0
    count = int((series == numerator_value).sum())
    return int(round(100 * count / base))


def evaluate_metric(df: pd.DataFrame, definition: MetricDefinition) -> int:
    """
    Evaluate a single MetricDefinition against a DataFrame.

    Returns an integer percentage in [0, 100]. For missing columns or empty
    bases this returns 0 rather than raising, so trends can skip gracefully.
    """
    cfg = definition.config
    if definition.type == "share_eq":
        column = str(cfg.get("from") or cfg.get("column"))
        value = cfg.get("value")
        return evaluate_share_eq(df, column, value)

    if definition.type == "share_in":
        column = str(cfg.get("from") or cfg.get("column"))
        values = cfg.get("values") or []
        return evaluate_share_in(df, column, list(values))

    if definition.type == "share_gt":
        column = str(cfg.get("from") or cfg.get("column"))
        threshold = float(cfg.get("threshold", 0))
        return evaluate_share_gt(df, column, threshold)

    if definition.type == "conditional_share":
        cond = cfg.get("condition") or {}
        num = cfg.get("numerator") or {}
        return evaluate_conditional_share(
            df,
            condition_column=str(cond.get("column")),
            condition_value=cond.get("equals"),
            numerator_column=str(num.get("column")),
            numerator_value=num.get("equals"),
        )

    # Unknown type: treat as 0 (should not normally happen due to filtering in load_wave_schema).
    return 0
