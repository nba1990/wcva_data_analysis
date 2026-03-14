from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.data_loader import load_dataset
from src.eda import (
    demand_and_outlook,
    executive_highlights,
    profile_summary,
    workforce_operations,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "wcva_sample_dataset.csv"
)


def _load_fixture_df() -> pd.DataFrame:
    """Load fixture via data_loader so derived columns (demand_direction, etc.) exist."""
    return load_dataset(str(FIXTURE_PATH))


def test_overview_headline_metrics_on_fixture() -> None:
    """
    Regression guard for key Overview / Executive metrics on a small fixture.

    The absolute values are not important beyond this test, but if they
    change unexpectedly it indicates that calculation logic, denominators
    or column mappings have been modified.
    """
    df = _load_fixture_df()
    dem = demand_and_outlook(df)
    wf = workforce_operations(df)
    prof = profile_summary(df)

    # Demand / finance story
    assert dem["demand_pct_increased"] == 66.7
    assert dem["financial_pct_deteriorated"] == 66.7
    assert dem["operating_pct_likely"] == 66.7

    # Workforce coverage headline row (has_volunteers / has_paid_staff)
    assert prof["has_volunteers_pct"] == 100.0
    assert prof["has_paid_staff_pct"] == 66.7

    # Workforce operations: recruitment difficulty and reserves
    assert wf["staff_rec_difficulty_pct"] >= 0.0
    assert wf["staff_ret_difficulty_pct"] >= 0.0
    assert wf["vol_rec_difficulty_pct"] > 0.0
    assert wf["finance_deteriorated_pct"] == 66.7


def test_executive_highlights_structure_on_fixture() -> None:
    """
    Executive summary highlights return a list of dicts with expected keys.
    Uses the same fixture as overview metrics; fixture includes multi-select
    columns (concerns, actions, rec/ret barriers, rec methods) so highlights run.
    """
    df = _load_fixture_df()
    highlights = executive_highlights(df)
    assert isinstance(highlights, list)
    assert len(highlights) >= 6
    for item in highlights:
        assert "rank" in item
        assert "title" in item
        assert "detail" in item
        assert "type" in item
        assert item["type"] in ("critical", "warning", "neutral")


def test_executive_highlights_output_structure_with_mock_data() -> None:
    """
    Executive highlights returns a list of dicts with rank, title, detail, type
    when EDA helpers return minimal valid structures.
    """
    # Minimal df (one row) so len(df) and n are defined
    df = pd.DataFrame(
        {
            "demand": ["Increased a lot"],
            "financial": ["Deteriorated a little"],
            "shortage_vol_rec": ["Yes"],
            "shortage_vol_ret": ["No"],
            "shortage_staff_rec": ["No"],
            "shortage_staff_ret": ["No"],
            "paidworkforce": ["Yes"],
            "financedeteriorate": ["Yes"],
            "reserves": ["Yes"],
            "usingreserves": ["No"],
            "workforce": ["Increased a lot"],
            "location_la_primary": ["Cardiff"],
        }
    )
    # Build minimal structures that executive_highlights expects
    concerns_df = pd.DataFrame(
        [
            {"label": "Income", "count": 1, "pct": 100.0},
            {"label": "Demand", "count": 1, "pct": 50.0},
        ]
    )
    actions_df = pd.DataFrame(
        [{"label": "Unplanned use of reserves", "count": 1, "pct": 100.0}]
    )
    rec_barriers_df = pd.DataFrame([{"label": "Time", "count": 1, "pct": 100.0}])
    ret_barriers_df = pd.DataFrame([{"label": "External", "count": 1, "pct": 100.0}])
    rec_methods_df = pd.DataFrame([{"label": "Social media", "count": 1, "pct": 100.0}])
    dem = {
        "demand_pct_increased": 100.0,
        "financial_pct_deteriorated": 100.0,
    }
    rec = {
        "pct_difficulty": 100.0,
        "pct_too_few": 100.0,
        "rec_barriers": rec_barriers_df,
        "rec_methods": rec_methods_df,
    }
    ret = {"ret_barriers": ret_barriers_df}
    wf = {
        "concerns": concerns_df,
        "actions": actions_df,
        "finance_deteriorated_pct": 100.0,
    }
    cross = None

    with (
        patch("src.eda.demand_and_outlook", return_value=dem),
        patch("src.eda.volunteer_recruitment_analysis", return_value=rec),
        patch("src.eda.volunteer_retention_analysis", return_value=ret),
        patch("src.eda.workforce_operations", return_value=wf),
        patch("src.eda.finance_recruitment_cross", return_value=cross),
    ):
        highlights = executive_highlights(df)
    assert isinstance(highlights, list)
    assert len(highlights) >= 6
    for item in highlights:
        assert (
            "rank" in item and "title" in item and "detail" in item and "type" in item
        )
        assert item["type"] in ("critical", "warning", "neutral")
