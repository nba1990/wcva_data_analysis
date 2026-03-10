from __future__ import annotations

import pandas as pd

from src.config import (
    WCVA_BRAND,
    get_palette,
    get_likert_colours,
    contrast_ratio,
    validate_palette_contrast,
    DEMAND_ORDER,
    FINANCIAL_ORDER,
    resolve_grouping,
    AltTextConfig,
    summarise_stacked_categories,
    format_group_summary,
    make_stacked_bar_alt,
)


def test_get_palette_and_likert_colours_modes() -> None:
    brand = get_palette("brand")
    accessible = get_palette("accessible")
    assert brand != accessible
    assert len(brand) >= 3 and len(accessible) >= 3

    likert_brand = get_likert_colours("brand")
    likert_accessible = get_likert_colours("accessible")
    assert likert_brand != likert_accessible


def test_contrast_ratio_and_validate_palette() -> None:
    navy = WCVA_BRAND["navy"]
    white = WCVA_BRAND["white"]
    ratio = contrast_ratio(navy, white)
    assert ratio > 3.0

    palette = get_palette("brand")
    result = validate_palette_contrast(palette, bg=white, min_ratio=3.0)
    assert set(result.keys()) == set(palette)
    # At least one colour should exceed the threshold
    assert any(r >= 3.0 for r in result.values())


def test_resolve_grouping_for_known_orders() -> None:
    grouper, order = resolve_grouping(DEMAND_ORDER)
    assert grouper is not None
    assert order is not None
    assert "Increased" in order

    # Financial order maps to a different grouping key
    grouper_fin, order_fin = resolve_grouping(FINANCIAL_ORDER)
    assert grouper_fin is not None
    assert order_fin is not None
    assert "Improved" in order_fin


def _sample_likert_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"value": "Increased a lot", "count": 10, "pct": 25.0},
            {"value": "Increased a little", "count": 15, "pct": 37.5},
            {"value": "Stayed the same", "count": 8, "pct": 20.0},
            {"value": "Decreased", "count": 7, "pct": 17.5},
        ]
    )


def test_summarise_stacked_categories_and_format_group_summary() -> None:
    df = _sample_likert_df()
    config = AltTextConfig(
        value_col="value",
        count_col="count",
        pct_col="pct",
        sample_size=40,
        chart_type="Stacked bar",
    )

    grouped = summarise_stacked_categories(
        df,
        value_col=config.value_col,
        count_col=config.count_col,
        pct_col=config.pct_col,
        grouper=None,
        group_order=None,
        drop_zero=True,
    )
    # Should preserve columns and aggregate to the same total
    assert {"group", "count", "pct"}.issubset(grouped.columns)
    assert grouped["count"].sum() == df["count"].sum()

    summary = format_group_summary(
        grouped,
        value_col="group",
        count_col="count",
        pct_col="pct",
        include_counts=True,
        include_percents=True,
    )
    assert "Increased a lot" in summary or "Increased" in summary


def test_make_stacked_bar_alt_includes_title_and_sample_size() -> None:
    df = _sample_likert_df()
    config = AltTextConfig(
        value_col="value",
        count_col="count",
        pct_col="pct",
        sample_size=40,
        chart_type="Stacked bar",
    )

    alt = make_stacked_bar_alt(
        df,
        title="Change in demand",
        config=config,
        grouper=None,
        group_order=None,
    )
    assert "Stacked bar: Change in demand." in alt
    assert "n=40" in alt

