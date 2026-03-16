# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

from src.wave_context import WAVE1_CONTEXT, WaveRegistry, build_trend_long, trend_series


def test_trend_series_and_build_trend_long_with_two_waves() -> None:
    # Use deep copies so we don't mutate the global WAVE1_CONTEXT
    wave1 = WAVE1_CONTEXT.model_copy(deep=True)
    wave2 = WAVE1_CONTEXT.model_copy(deep=True)
    wave2.meta.wave_label = "Wave 2"
    wave2.meta.wave_number = 2
    wave2.demand.headline.increasing_demand_for_services_pct = (
        wave1.demand.headline.increasing_demand_for_services_pct + 5
    )

    registry = WaveRegistry(waves={"Wave 1": wave1, "Wave 2": wave2})

    series = trend_series(
        registry, "demand.headline.increasing_demand_for_services_pct"
    )
    assert [p["wave_number"] for p in series] == [1, 2]
    assert [p["value"] for p in series] == [
        wave1.demand.headline.increasing_demand_for_services_pct,
        wave2.demand.headline.increasing_demand_for_services_pct,
    ]

    long_df = build_trend_long(
        registry,
        metrics=[
            {
                "id": "demand_increase",
                "label": "Demand increased",
                "section": "Demand & finance",
                "attr_path": "demand.headline.increasing_demand_for_services_pct",
            }
        ],
    )

    assert set(long_df["metric_id"]) == {"demand_increase"}
    assert long_df["wave_number"].tolist() == [1, 2]


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
