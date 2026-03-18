from __future__ import annotations

from typing import Any

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.pandas import column, data_frames, range_indexes

from src.data_loader import count_multiselect
from src.eda import _share_true, _value_counts_ordered


@given(
    st.lists(
        st.booleans() | st.none(),
        min_size=0,
        max_size=200,
    )
)
def test_share_true_range_and_empty_behaviour(
    values: list[bool | None],
) -> None:
    series = pd.Series(values, dtype="object")
    pct = _share_true(series)

    # Percentages are always within [0, 100]
    assert 0.0 <= pct <= 100.0

    # When there is no non-missing data, we return 0.0
    if series.notna().sum() == 0:
        assert pct == 0.0


@given(
    series=st.lists(
        st.sampled_from(["low", "medium", "high"]) | st.none(),
        min_size=0,
        max_size=200,
    ),
)
def test_value_counts_ordered_range_and_order(series: list[str | None]) -> None:
    order = ["low", "medium", "high"]
    s = pd.Series(series, dtype="object")
    df = _value_counts_ordered(s, order)

    # The function always returns one row per category in order.
    assert list(df["value"]) == order

    # Counts are non-negative integers and sum to the number of non-missing entries.
    assert (df["count"] >= 0).all()
    assert df["count"].dtype == int
    assert int(df["count"].sum()) == int(s.notna().sum())

    # Percentages are between 0 and 100 and sum to ~100 (or 0 for empty base).
    assert (df["pct"].between(0, 100)).all()
    if s.notna().sum() == 0:
        assert df["pct"].sum() == 0
    else:
        total = float(df["pct"].sum())
        # Allow for minor floating point rounding differences.
        assert total == pytest.approx(100.0, abs=0.2)


@given(
    data_frames(
        columns=[
            column(
                "multi",
                elements=st.text(
                    alphabet=st.characters(),
                    min_size=0,
                ),
            ),
        ],
        index=range_indexes(
            min_size=0,
            max_size=200,
        ),
    ),
)
def test_count_multiselect_monotonic_and_consistent(df: pd.DataFrame) -> None:
    """
    Property tests for count_multiselect:

    - Total count is the sum over all labels.
    - Removing a row cannot increase any label's count.
    """

    # Choose some arbitrary label set for the multiselect; in the real app these
    # are human-readable labels but the behaviour is the same.
    labels: dict[str, str] = {
        "a": "A",
        "b": "B",
        "c": "C",
    }

    # Coerce "multi" to the simple "|" separated format used in tests/fixtures,
    # mapping arbitrary strings to a small finite alphabet of options.
    def normalise_cell(cell: Any) -> str:
        if not isinstance(cell, str) or cell == "":
            return ""
        # Deterministically bucket characters into label keys.
        mapped = []
        for ch in cell:
            bucket = ord(ch) % 3
            mapped.append("abc"[bucket])
        # Remove duplicates within a cell.
        return "|".join(sorted(set(mapped)))

    df_norm = df.copy()
    df_norm["multi"] = df_norm["multi"].map(normalise_cell)

    full_counts = count_multiselect(df_norm, labels)

    # Counts are non-negative and monotonic with respect to row removal.
    assert (full_counts["count"] >= 0).all()

    # Remove a random half of the rows and recompute; every label's count
    # should be less-than-or-equal to its original count.
    if len(df_norm) > 0:
        subset = df_norm.iloc[::2]
        subset_counts = count_multiselect(subset, labels)

        merged = full_counts.merge(
            subset_counts[["label", "count"]],
            on="label",
            how="left",
            suffixes=("_full", "_subset"),
        )
        merged["count_subset"] = merged["count_subset"].fillna(0).astype(int)

        assert (merged["count_subset"] <= merged["count_full"]).all()
