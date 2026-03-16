# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd

from src.wave_schema import (
    MetricDefinition,
    evaluate_conditional_share,
    evaluate_metric,
    evaluate_share_eq,
    evaluate_share_gt,
    evaluate_share_in,
    load_wave_schema,
)


def test_evaluate_share_eq_basic() -> None:
    df = pd.DataFrame({"status": ["Yes", "No", "Yes", None]})
    # Two of three non-missing rows are "Yes" → 66.7 → 67
    assert evaluate_share_eq(df, "status", "Yes") == 67
    # Missing column yields 0 rather than raising.
    assert evaluate_share_eq(df, "missing", "Yes") == 0


def test_evaluate_share_in_basic() -> None:
    df = pd.DataFrame({"tier": ["High", "Medium", "Low", "Low", None]})
    # Three of four non-missing rows are in {"High", "Low"} → 75%
    assert evaluate_share_in(df, "tier", ["High", "Low"]) == 75
    # Empty values list yields 0.
    assert evaluate_share_in(df, "tier", []) == 0


def test_evaluate_share_gt_basic() -> None:
    df = pd.DataFrame({"count": [0, 1, 2, None]})
    # Two of three non-missing rows are > 0 → 66.7 → 67
    assert evaluate_share_gt(df, "count", 0) == 67
    # Missing column yields 0.
    assert evaluate_share_gt(df, "missing", 0) == 0


def test_evaluate_conditional_share_basic() -> None:
    df = pd.DataFrame(
        {
            "has_reserves": ["Yes", "Yes", "No", "Yes"],
            "using_reserves": ["Yes", "No", "Yes", None],
        }
    )
    # Among rows where has_reserves == Yes, one of two non-missing using_reserves is Yes → 50%
    pct = evaluate_conditional_share(
        df,
        condition_column="has_reserves",
        condition_value="Yes",
        numerator_column="using_reserves",
        numerator_value="Yes",
    )
    assert pct == 50


def test_evaluate_metric_dispatches_on_type() -> None:
    df = pd.DataFrame({"flag": ["A", "B", "A"]})

    m_eq = MetricDefinition(
        id="m_eq", type="share_eq", config={"from": "flag", "value": "A"}
    )
    m_in = MetricDefinition(
        id="m_in", type="share_in", config={"from": "flag", "values": ["A", "B"]}
    )
    m_gt = MetricDefinition(
        id="m_gt", type="share_gt", config={"from": "numeric", "threshold": 0}
    )
    m_cond = MetricDefinition(
        id="m_cond",
        type="conditional_share",
        config={
            "condition": {"column": "flag", "equals": "A"},
            "numerator": {"column": "flag", "equals": "A"},
        },
    )

    # share_eq: 2 of 3 rows == "A" → 66.7 → 67
    assert evaluate_metric(df, m_eq) == 67
    # share_in: all 3 rows in {"A", "B"} → 100
    assert evaluate_metric(df, m_in) == 100
    # share_gt: missing numeric column → 0
    assert evaluate_metric(df, m_gt) == 0
    # conditional_share: among rows where flag == "A", all rows also satisfy numerator → 100
    assert evaluate_metric(df, m_cond) == 100


def test_load_wave_schema_wave2_basic() -> None:
    schema = load_wave_schema("wave2")
    assert schema.wave_label in {"Wave 2", "wave2"}
    assert schema.wave_number == 2
    # Sanity-check that a few known metrics are present
    for key in [
        "finance_deteriorated_costs",
        "has_reserves",
        "has_volunteers",
        "has_paid_staff",
    ]:
        assert key in schema.metrics


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
