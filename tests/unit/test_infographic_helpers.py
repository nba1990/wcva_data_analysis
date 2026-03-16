# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

from src.infographic import (
    _build_metrics,
    _classify_severity,
    _compute_gauge_colour,
    _compute_trend,
)


def test_classify_severity_risk_metric_thresholds() -> None:
    assert _classify_severity(10, higher_is_good=False) == "positive"
    assert _classify_severity(45, higher_is_good=False) == "mixed"
    assert _classify_severity(75, higher_is_good=False) == "concerning"


def test_compute_trend_neutral_and_directions() -> None:
    # No previous value -> neutral
    symbol, css = _compute_trend(50, None, higher_is_good=False)
    assert symbol == "●"
    assert css == "wcva-trend-neutral"

    # Risk metric: increase is bad -> up arrow
    symbol, css = _compute_trend(70, 50, higher_is_good=False)
    assert symbol == "▲"
    assert css == "wcva-trend-up"

    # Risk metric: decrease is good -> down arrow
    symbol, css = _compute_trend(40, 60, higher_is_good=False)
    assert symbol == "▼"
    assert css == "wcva-trend-down"


def test_compute_gauge_colour_aligns_with_severity() -> None:
    # For risk metrics, low values -> teal, high values -> coral
    assert _compute_gauge_colour(20, higher_is_good=False) != _compute_gauge_colour(
        80, higher_is_good=False
    )


def test_build_metrics_basic_structure() -> None:
    dem = {
        "demand_pct_increased": 60.0,
        "financial_pct_deteriorated": 40.0,
    }
    rec = {
        "pct_too_few": 63.6,
        "pct_difficulty": 53.3,
    }
    ret = {
        "pct_difficulty": 34.3,
    }

    metrics = _build_metrics(111, dem, rec, ret)

    # Six cards with expected IDs and keys
    ids = {m["id"] for m in metrics}
    assert ids == {"orgs", "demand", "finance", "too_few", "rec_diff", "ret_diff"}

    demand_card = next(m for m in metrics if m["id"] == "demand")
    assert demand_card["gauge_fill"] == 60.0
    assert "severity" in demand_card
    assert demand_card["trend_symbol"] in {"▲", "▼", "●"}


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
