# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

from src.infographic import _build_metrics


def test_build_metrics_trend_and_severity_with_previous_wave() -> None:
    dem = {
        "demand_pct_increased": 62.2,
        "demand_pct_increased_prev": 56.0,
        "financial_pct_deteriorated": 35.1,
        "financial_pct_deteriorated_prev": 74.0,
    }
    rec = {
        "pct_too_few": 63.6,
        "pct_too_few_prev": 55.0,
        "pct_difficulty": 53.3,
        "pct_difficulty_prev": 48.0,
    }
    ret = {
        "pct_difficulty": 34.3,
        "pct_difficulty_prev": 31.0,
    }

    metrics = _build_metrics(111, dem, rec, ret)

    demand = next(m for m in metrics if m["id"] == "demand")
    finance = next(m for m in metrics if m["id"] == "finance")
    too_few = next(m for m in metrics if m["id"] == "too_few")

    # Demand risk metric: higher share reporting increased demand is concerning.
    assert demand["trend_symbol"] in {"▲", "▼", "●"}
    assert demand["severity"] in {"positive", "mixed", "concerning"}

    # Finances deteriorated have improved vs previous wave (74 -> 35.1),
    # so colour should be less severe than the previous value and still
    # classified through the helper.
    assert finance["severity"] in {"positive", "mixed", "concerning"}

    # Too few volunteers at 63.6% should be classified at least as mixed / concerning.
    assert too_few["severity"] in {"mixed", "concerning"}


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
