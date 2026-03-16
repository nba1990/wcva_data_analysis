# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

from src.data_loader import _derive_columns
from src.eda import (
    demand_and_outlook,
    profile_summary,
    volunteer_recruitment_analysis,
    workforce_operations,
)
from src.wave_context import (
    WAVE1_CONTEXT,
    WaveContext,
    WaveRegistry,
    build_wave_context_from_df,
    compare_demand_increase,
    pct_point_change,
    trend_series,
)


def test_wavecontext_validation_enforces_pct_ranges() -> None:
    # Using the existing WAVE1_CONTEXT as a known-good example
    assert isinstance(WAVE1_CONTEXT, WaveContext)
    assert (
        0
        <= WAVE1_CONTEXT.finance.headline.financial_position_deteriorated_due_to_rising_costs_pct
        <= 100
    )


def test_build_wave_context_from_df_matches_eda_outputs(tiny_df) -> None:
    # Derive the same aggregates that build_wave_context_from_df uses
    derived = _derive_columns(tiny_df.copy())
    # Ensure required columns exist with simple defaults
    for col, default in {
        "socialenterprise": "No",
        "paidworkforce": "Yes",
        "wales_scope": "All Wales",
    }.items():
        if col not in derived.columns:
            derived[col] = default
    prof = profile_summary(derived)
    dem = demand_and_outlook(derived)
    wf = workforce_operations(derived)
    rec = volunteer_recruitment_analysis(derived)

    ctx = build_wave_context_from_df(derived, wave_label="Wave X", wave_number=99)

    assert ctx.meta.wave_response_count == prof["n"]
    assert ctx.demand.headline.increasing_demand_for_services_pct == int(
        round(dem["demand_pct_increased"])
    )
    assert (
        ctx.finance.headline.financial_position_deteriorated_due_to_rising_costs_pct
        == int(round(wf["finance_deteriorated_pct"]))
    )
    assert ctx.workforce.headline.too_few_volunteers_pct == int(
        round(rec["pct_too_few"])
    )


def test_wave_registry_and_trend_series_round_trip() -> None:
    registry = WaveRegistry(waves={"Wave 1": WAVE1_CONTEXT})
    series = trend_series(
        registry, "demand.headline.increasing_demand_for_services_pct"
    )

    assert len(series) == 1
    point = series[0]
    assert point["wave_label"] == "Wave 1"
    assert (
        point["value"]
        == WAVE1_CONTEXT.demand.headline.increasing_demand_for_services_pct
    )


def test_pct_point_change() -> None:
    """Percentage-point change is new minus old."""
    assert pct_point_change(40, 50) == 10
    assert pct_point_change(50, 40) == -10
    assert pct_point_change(66, 66) == 0


def test_compare_helpers_use_pct_point_change() -> None:
    first = WAVE1_CONTEXT
    # Synthetic \"latest\" wave with different demand percentage
    latest = first.model_copy()
    latest.demand.headline.increasing_demand_for_services_pct = (
        first.demand.headline.increasing_demand_for_services_pct + 5
    )

    result = compare_demand_increase(first, latest)
    assert result["change_pct_points"] == pct_point_change(
        result["old_value"], result["new_value"]
    )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
