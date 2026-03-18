from __future__ import annotations

from src.wave_context import (
    TREND_METRICS,
    WaveContext,
    WaveRegistry,
    build_trend_long,
    build_trend_pivot,
    summarise_trend_changes,
    trend_series,
)


def make_registry_with_partial_wave2() -> WaveRegistry:
    """Build a minimal WaveRegistry where some metrics are missing on Wave 2."""
    from src.wave_context import WAVE1_CONTEXT

    # Start from the real Wave 1 context and construct a pared-down Wave 2
    # that only has a subset of attributes populated.
    wave1 = WAVE1_CONTEXT

    class DummyWave2(WaveContext):
        """Lightweight clone of Wave 1 used as a stand-in for Wave 2."""

    wave2 = DummyWave2.model_validate(wave1.model_dump())
    # Ensure Wave 2 really is a separate wave in metadata so ordering and
    # labelling behave as expected in trend helpers.
    wave2.meta.wave_label = "Wave 2"
    wave2.meta.wave_number = wave1.meta.wave_number + 1
    # Deliberately remove a couple of attributes from Wave 2 so that some
    # TREND_METRICS attr_paths resolve to None and should be skipped.
    wave2.headline_kpis.financial_health.has_financial_reserves_pct = None
    wave2.headline_kpis.financial_health.using_reserves_among_those_with_reserves_pct = None

    return WaveRegistry(waves={"Wave 1": wave1, "Wave 2": wave2})


def test_trend_series_skips_missing_metrics() -> None:
    registry = make_registry_with_partial_wave2()

    # Metric where both waves have values.
    full_attr = "demand.headline.increasing_demand_for_services_pct"
    series_full = trend_series(registry, full_attr)
    assert len(series_full) == 2
    assert [p["wave_label"] for p in series_full] == ["Wave 1", "Wave 2"]

    # Metric path that does not exist anywhere should simply return an empty
    # series rather than raising.
    missing_attr = "does.not.exist.anywhere"
    series_missing = trend_series(registry, missing_attr)
    assert series_missing == []


def test_build_trend_long_handles_partial_series() -> None:
    registry = make_registry_with_partial_wave2()

    metrics = [m for m in TREND_METRICS if m["id"] == "demand_increase"]

    df = build_trend_long(registry, metrics=metrics)

    # demand_increase should have two rows (Wave 1 and Wave 2).
    demand_rows = df[df["metric_id"] == "demand_increase"]
    assert set(demand_rows["wave_label"]) == {"Wave 1", "Wave 2"}
    # No unexpected metric ids appear.
    assert set(df["metric_id"]) == {"demand_increase"}


def test_build_trend_pivot_and_summarise_trend_changes() -> None:
    registry = make_registry_with_partial_wave2()

    # Use the default TREND_METRICS but focus assertions on a couple.
    df_long = build_trend_long(registry)
    pivot = build_trend_pivot(df_long)

    # Pivot should have one row per wave; n_organisations comes from meta.
    assert set(pivot["Wave"]) == {"Wave 1", "Wave 2"}
    assert "n_organisations" in pivot.columns
    # All n_organisations values should be positive integers.
    assert (pivot["n_organisations"] > 0).all()

    # summarise_trend_changes should only emit summaries for metrics
    # that have data; requesting a non-existent metric id should be a no-op.
    summaries = summarise_trend_changes(
        df_long, metric_ids=["demand_increase", "not_a_real_metric"]
    )

    assert "demand_increase" in summaries
    demand_summary = summaries["demand_increase"]
    assert demand_summary["first_wave"] == "Wave 1"
    assert demand_summary["latest_wave"] == "Wave 2"

    # Unknown metric ids should simply be ignored.
    assert "not_a_real_metric" not in summaries
