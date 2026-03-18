# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd

from src.config import (
    DEFAULT_LA_CONTEXT_PATH,
    DEMAND_ORDER,
    FINANCIAL_ORDER,
    SAMPLE_DATASET_PATH,
    WCVA_BRAND,
    AltTextConfig,
    contrast_ratio,
    display_runtime_source,
    format_group_summary,
    get_demo_output_mode,
    get_likert_colours,
    get_palette,
    make_pattern_grouper,
    make_stacked_bar_alt,
    mask_runtime_value,
    normalise_label,
    resolve_dataset_source,
    resolve_grouping,
    resolve_la_context_source,
    summarise_stacked_categories,
    validate_palette_contrast,
)


def test_normalise_label() -> None:
    assert normalise_label("  Increased a lot  ") == "increased a lot"
    assert normalise_label("Stayed the same") == "stayed the same"
    # Curly apostrophe normalised to straight
    assert "’" not in normalise_label("Organisation's")


def test_make_pattern_grouper() -> None:
    grouper = make_pattern_grouper(
        [("Up", ("increase", "increased")), ("Down", ("decrease",))],
        default="Other",
    )
    assert grouper("Increased a lot") == "Up"
    assert grouper("Decreased a little") == "Down"
    assert grouper("Stayed the same") == "Other"


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


def test_resolve_dataset_source_prefers_env_path(monkeypatch, tmp_path) -> None:
    dataset = tmp_path / "wave.csv"
    dataset.write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setenv("WCVA_DATASET_PATH", str(dataset))
    monkeypatch.delenv("WCVA_DATASET_URL", raising=False)

    source = resolve_dataset_source()

    assert source.value == str(dataset)
    assert source.source_type == "env_path"
    assert source.is_demo is False


def test_resolve_dataset_source_falls_back_to_sample_fixture(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.delenv("WCVA_DATASET_PATH", raising=False)
    monkeypatch.delenv("WCVA_DATASET_URL", raising=False)

    # Ensure the default dataset path is treated as missing, even if a real
    # dataset exists in the developer's working tree. Point it to a
    # non-existent path under a temporary root so we exercise the
    # sample-data fallback branch deterministically.
    fake_default = tmp_path / "datasets" / "missing_wave.csv"
    monkeypatch.setattr("src.config.DEFAULT_DATASET_PATH", fake_default, raising=False)

    source = resolve_dataset_source()

    assert source.value == str(SAMPLE_DATASET_PATH)
    assert source.source_type == "sample_path"
    assert source.is_demo is True
    assert source.exists is True


def test_resolve_la_context_source_defaults_to_public_reference(monkeypatch) -> None:
    monkeypatch.delenv("WCVA_LA_CONTEXT_PATH", raising=False)
    monkeypatch.delenv("WCVA_LA_CONTEXT_URL", raising=False)

    source = resolve_la_context_source()

    assert source.value == str(DEFAULT_LA_CONTEXT_PATH)
    assert source.source_type == "default_path"
    assert source.is_demo is False
    assert source.exists is True


def test_mask_runtime_value_redacts_http_urls() -> None:
    url = "https://nextclouds.example.com/s/ASJDKJAHSDKJASKJDHSAD/download"

    masked = mask_runtime_value(url)

    assert masked == "https://nextclouds.example.com/s/[redacted]/download"
    assert "ASJDKJAHSDKJASKJDHSAD" not in masked


def test_display_runtime_source_keeps_paths_but_masks_urls(monkeypatch) -> None:
    monkeypatch.setenv(
        "WCVA_DATASET_URL",
        "https://nextclouds.example.com/s/ASJDKJAHSDKJASKJDHSAD/download",
    )

    source = resolve_dataset_source()

    assert display_runtime_source(source) == (
        "https://nextclouds.example.com/s/[redacted]/download"
    )
    assert source.attempted == (
        "env:WCVA_DATASET_URL -> https://nextclouds.example.com/s/[redacted]/download",
    )


def test_get_demo_output_mode_defaults_to_separate_outputs(monkeypatch) -> None:
    monkeypatch.delenv("WCVA_DEMO_OUTPUT_MODE", raising=False)
    assert get_demo_output_mode() == "separate_outputs"


def test_get_demo_output_mode_accepts_banner_only(monkeypatch) -> None:
    monkeypatch.setenv("WCVA_DEMO_OUTPUT_MODE", "banner_only")
    assert get_demo_output_mode() == "banner_only"


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
