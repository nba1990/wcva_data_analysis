from __future__ import annotations

import pandas as pd

from src.config import CONCERNS_LABELS, StreamlitAppUISharedConfigState
from src.filters import apply_filters


def make_ui() -> StreamlitAppUISharedConfigState:
    return StreamlitAppUISharedConfigState(
        size_options=[],
        scope_options=[],
        la_scope_options=[],
        activity_options=[],
        paid_staff_options=[],
        concern_label_options=[],
    )


def test_apply_filters_defaults_return_full_df() -> None:
    df_full = pd.DataFrame(
        {
            "org_size": ["Small", "Medium"],
            "wales_scope": ["Local", "National"],
            "location_la_primary": ["A", "B"],
            "mainactivity": ["X", "Y"],
            "paidworkforce": ["Yes", "No"],
        }
    )
    ui = make_ui()
    ui.selected_size = "All"
    ui.selected_scope = "All"
    ui.selected_la_scope = "All"
    ui.selected_activity = "All"
    ui.selected_paid_staff = "All"
    ui.selected_concerns = []

    result = apply_filters(df_full, ui)
    assert len(result) == len(df_full)


def test_apply_filters_by_size_and_paid_staff() -> None:
    df_full = pd.DataFrame(
        {
            "org_size": ["Small", "Medium", "Small"],
            "wales_scope": ["Local", "National", "Local"],
            "location_la_primary": ["A", "B", "A"],
            "mainactivity": ["X", "Y", "X"],
            "paidworkforce": ["Yes", "No", "Yes"],
        }
    )
    ui = make_ui()
    ui.selected_size = "Small"
    ui.selected_scope = "All"
    ui.selected_la_scope = "All"
    ui.selected_activity = "All"
    ui.selected_paid_staff = "Has paid staff"
    ui.selected_concerns = []

    result = apply_filters(df_full, ui)
    # Only rows 0 and 2 are Small; both have paidworkforce == Yes
    assert len(result) == 2
    assert set(result.index) == {0, 2}


def test_apply_filters_by_concerns_any_match() -> None:
    # Map one concern label to a column and ensure we keep rows where that column is non-null.
    key, label = next(iter(CONCERNS_LABELS.items()))
    df_full = pd.DataFrame(
        {
            "org_size": ["Small", "Small"],
            "wales_scope": ["Local", "Local"],
            "location_la_primary": ["A", "A"],
            "mainactivity": ["X", "X"],
            "paidworkforce": ["Yes", "Yes"],
            key: [1.0, None],
        }
    )
    ui = make_ui()
    ui.selected_size = "All"
    ui.selected_scope = "All"
    ui.selected_la_scope = "All"
    ui.selected_activity = "All"
    ui.selected_paid_staff = "All"
    ui.selected_concerns = [label]

    result = apply_filters(df_full, ui)
    # Only first row has the concern column non-null
    assert list(result.index) == [0]


def test_apply_filters_multiple_concerns_and_la_and_paid_staff() -> None:
    # Use two concern labels and ensure we keep rows that match either concern,
    # while also honouring LA + paid staff filters.
    items = list(CONCERNS_LABELS.items())
    (col1, label1), (col2, label2) = items[0], items[1]

    df_full = pd.DataFrame(
        {
            "org_size": ["Small", "Small", "Medium", "Small"],
            "wales_scope": ["Local", "Local", "National", "Local"],
            "location_la_primary": ["A", "A", "A", "B"],
            "mainactivity": ["X", "X", "Y", "X"],
            "paidworkforce": ["Yes", "No", "Yes", "Yes"],
            # Row 0: matches concern 1
            # Row 1: matches concern 2
            # Row 2: matches both concerns
            # Row 3: matches neither concern
            col1: [1.0, None, 1.0, None],
            col2: [None, 1.0, 1.0, None],
        }
    )

    ui = make_ui()
    ui.selected_size = "All"
    ui.selected_scope = "All"
    ui.selected_la_scope = "A"
    ui.selected_activity = "All"
    ui.selected_paid_staff = "Has paid staff"
    ui.selected_concerns = [label1, label2]

    result = apply_filters(df_full, ui)

    # With LA == "A" and Has paid staff, only rows 0 and 2 are eligible.
    # Both have at least one of the selected concern columns non-null.
    assert set(result.index) == {0, 2}


def test_apply_filters_concerns_with_missing_values() -> None:
    # When concern columns contain NaNs, only rows with non-missing values in
    # at least one selected concern column should be retained.
    key, label = next(iter(CONCERNS_LABELS.items()))
    df_full = pd.DataFrame(
        {
            "org_size": ["Small", "Small", "Small"],
            "wales_scope": ["Local", "Local", "Local"],
            "location_la_primary": ["A", "A", "A"],
            "mainactivity": ["X", "X", "X"],
            "paidworkforce": ["Yes", "Yes", "Yes"],
            key: [1.0, float("nan"), None],
        }
    )

    ui = make_ui()
    ui.selected_size = "All"
    ui.selected_scope = "All"
    ui.selected_la_scope = "All"
    ui.selected_activity = "All"
    ui.selected_paid_staff = "All"
    ui.selected_concerns = [label]

    result = apply_filters(df_full, ui)
    # Only row 0 has a non-missing concern value.
    assert list(result.index) == [0]
