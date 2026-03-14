from __future__ import annotations

import pandas as pd

from src.config import LA_TO_REGION, MULTI_SELECT_GROUPS
from src.data_loader import (
    _clean,
    _derive_columns,
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
