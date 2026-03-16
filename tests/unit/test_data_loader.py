# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import pandas as pd

from src.config import LA_TO_REGION, MULTI_SELECT_GROUPS
from src.data_loader import (
    _clean,
    _derive_columns,
    check_runtime_assets,
    count_multiselect,
    count_multiselect_by_segment,
    data_quality_profile,
)


def test_clean_converts_empty_strings_and_numeric_columns() -> None:
    df = pd.DataFrame(
        {
            "text": [" a ", "", None],
            "peopleemploy": ["10", "not-a-number", None],
        }
    )

    cleaned = _clean(df.copy())

    # First entry should be stripped; second should become NaN; third also coerced to NaN
    assert cleaned["text"].iloc[0] == "a"
    assert pd.isna(cleaned["text"].iloc[1])
    assert pd.isna(cleaned["text"].iloc[2])

    assert cleaned["peopleemploy"].iloc[0] == 10.0
    assert pd.isna(cleaned["peopleemploy"].iloc[1])
    assert pd.isna(cleaned["peopleemploy"].iloc[2])


def test_derive_columns_adds_region_and_flags(tiny_df: pd.DataFrame) -> None:
    # Ensure mapping contains the LAs we use in the fixture
    assert {"Cardiff", "Swansea"}.issubset(LA_TO_REGION.keys())

    derived = _derive_columns(tiny_df.copy())

    # Region column derived from local authority
    assert "region" in derived.columns
    assert set(derived["region"].dropna()) <= set(LA_TO_REGION.values())

    # Boolean difficulty/finance flags
    for col in [
        "has_vol_rec_difficulty",
        "has_vol_ret_difficulty",
        "has_staff_rec_difficulty",
        "has_staff_ret_difficulty",
        "finance_deteriorated",
    ]:
        assert col in derived.columns
        assert derived[col].dtype == bool

    # Multi-select counts are present for all configured groups
    for group_name in MULTI_SELECT_GROUPS:
        col_name = f"{group_name}_count"
        assert col_name in derived.columns


def test_count_multiselect_basic() -> None:
    df = pd.DataFrame(
        {
            "a": [1, None, 2],
            "b": [None, None, 3],
        }
    )
    labels = {"a": "Option A", "b": "Option B"}

    result = count_multiselect(df, labels)

    assert list(result["label"]) == ["Option A", "Option B"]
    assert result.loc[result["label"] == "Option A", "count"].item() == 2
    assert result.loc[result["label"] == "Option B", "count"].item() == 1


def test_count_multiselect_by_segment() -> None:
    df = pd.DataFrame(
        {
            "seg": ["X", "X", "Y", "Y"],
            "c1": [1, None, 1, None],
            "c2": [None, None, 2, 2],
        }
    )
    labels = {"c1": "Col 1", "c2": "Col 2"}

    result = count_multiselect_by_segment(df, labels, "seg")

    # We expect percentage shares within each segment
    row_c1 = result[result["label"] == "Col 1"].iloc[0]
    row_c2 = result[result["label"] == "Col 2"].iloc[0]

    # For segment X: 1 of 2 rows selects c1 -> 50%
    assert row_c1["X"] == 50.0
    # For segment Y: 1 of 2 rows selects c1 -> 50%
    assert row_c1["Y"] == 50.0

    # For c2, only segment Y has selections: 2 of 2 rows -> 100%
    assert row_c2["Y"] == 100.0


def test_count_multiselect_by_segment_empty_segment() -> None:
    """When a segment has no rows, percentage is 0 (no divide-by-zero)."""
    df = pd.DataFrame(
        {"seg": ["A"], "c1": [1]},
    )
    labels = {"c1": "Col 1"}
    result = count_multiselect_by_segment(df, labels, "seg")
    assert result.shape[0] == 1
    assert result.loc[result["label"] == "Col 1", "A"].item() == 100.0


def test_data_quality_profile_structure() -> None:
    """Data quality profile returns expected keys and handles empty df."""
    df = pd.DataFrame(
        {
            "org_size": ["Small", "Medium"],
            "location_la_primary": ["Cardiff", "Swansea"],
            "demand": ["Increased a lot", None],
        }
    )
    profile = data_quality_profile(df)
    assert profile["n_rows"] == 2
    assert profile["n_cols"] == 3
    assert "missing_by_col" in profile
    assert "missing_pct_by_col" in profile
    assert "block_completeness" in profile
    assert profile["org_size_missing"] == 0
    assert profile["complete_pct"] >= 0


def test_check_runtime_assets_reports_required_and_optional_files(tmp_path) -> None:
    project_root = tmp_path
    dataset_path = project_root / "runtime-data" / "WCVA_W2_Anonymised_Dataset.csv"
    la_context_path = project_root / "runtime-data" / "la_context_wales.csv"
    streamlit_config = project_root / ".streamlit" / "config.toml"
    mindmap_html = (
        project_root
        / "references/SROI_Wales_Voluntary_Sector/docs/WCVA_Text_Interactive_MindMap.html"
    )

    dataset_path.parent.mkdir(parents=True)
    streamlit_config.parent.mkdir(parents=True)
    mindmap_html.parent.mkdir(parents=True)

    dataset_path.write_text("a,b\n1,2\n", encoding="utf-8")
    streamlit_config.write_text("[server]\nheadless = true\n", encoding="utf-8")
    mindmap_html.write_text("<html></html>", encoding="utf-8")

    result = check_runtime_assets(
        project_root=project_root,
        dataset_path=dataset_path,
        la_context_path=la_context_path,
    )

    assert result["all_required_present"] is True
    assert result["missing_required"] == []
    assert "Local authority context CSV" in result["missing_optional"]
    assert len(result["required"]) == 2
    assert len(result["optional"]) == 3


def test_check_runtime_assets_flags_missing_required_files(tmp_path) -> None:
    result = check_runtime_assets(
        project_root=tmp_path,
        dataset_path=tmp_path / "runtime-data" / "missing.csv",
        la_context_path=tmp_path / "runtime-data" / "la_context_wales.csv",
    )

    assert result["all_required_present"] is False
    assert "Wave 2 dataset source" in result["missing_required"]
    assert "Streamlit config" in result["missing_required"]


def test_check_runtime_assets_accepts_dataset_url_without_local_file(tmp_path) -> None:
    streamlit_config = tmp_path / ".streamlit" / "config.toml"
    streamlit_config.parent.mkdir(parents=True)
    streamlit_config.write_text("[server]\nheadless = true\n", encoding="utf-8")

    result = check_runtime_assets(
        project_root=tmp_path,
        dataset_path=tmp_path / "runtime-data" / "missing.csv",
        dataset_url="https://example.invalid/wcva.csv",
    )

    assert result["all_required_present"] is True
    assert result["missing_required"] == []
    assert result["required"][0]["path"] == "https://example.invalid/[redacted]"


def test_read_csv_from_private_url_redacts_runtime_error(monkeypatch) -> None:
    import pandas as pd

    from src.config import RuntimeDataSource
    from src.data_loader import _read_csv_from_source

    def _boom(*args, **kwargs):
        raise ValueError("simulated failure")

    monkeypatch.setattr(pd, "read_csv", _boom)

    source = RuntimeDataSource(
        label="Wave dataset",
        value="https://nextclouds.example.com/s/ASJDKJAHSDKJASKJDHSAD/download",
        source_type="env_url",
        exists=True,
        is_url=True,
    )

    try:
        _read_csv_from_source(source)
    except RuntimeError as exc:
        message = str(exc)
        assert "nextclouds.example.com" in message
        assert "ASJDKJAHSDKJASKJDHSAD" not in message
    else:
        raise AssertionError("Expected RuntimeError for invalid URL test source")


def test_check_runtime_assets_marks_demo_mode_for_sample_fixture(
    tmp_path, monkeypatch
) -> None:
    streamlit_config = tmp_path / ".streamlit" / "config.toml"
    streamlit_config.parent.mkdir(parents=True)
    streamlit_config.write_text("[server]\nheadless = true\n", encoding="utf-8")

    # Ensure the default dataset path is treated as missing so that
    # resolve_dataset_source falls back to the bundled sample fixture and
    # marks the app as running in demo mode, independently of any real
    # dataset that may exist in the developer's working tree.
    fake_default = tmp_path / "datasets" / "missing_wave.csv"
    monkeypatch.setattr("src.config.DEFAULT_DATASET_PATH", fake_default, raising=False)
    result = check_runtime_assets(project_root=tmp_path)

    assert result["app_mode"] == "demo"
    assert result["dataset_source"].is_demo is True
    assert result["required"][0]["mode"] == "demo"


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
