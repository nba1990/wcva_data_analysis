from __future__ import annotations

import pandas as pd

from src.data_loader import _derive_columns
from src.eda import (
    demand_and_outlook,
    volunteer_recruitment_analysis,
    volunteer_retention_analysis,
    workforce_operations,
    finance_recruitment_cross,
)


def test_demand_and_outlook_basic_percentages(tiny_df: pd.DataFrame) -> None:
    derived = _derive_columns(tiny_df.copy())
    dem = demand_and_outlook(derived)

    # Percentages should be between 0 and 100 and sum not constrained
    assert 0 <= dem["demand_pct_increased"] <= 100
    assert 0 <= dem["financial_pct_deteriorated"] <= 100
    assert 0 <= dem["operating_pct_likely"] <= 100

    # Under our fixture, at least one organisation reports increased demand
    assert dem["demand_pct_increased"] > 0


def test_volunteer_recruitment_analysis_pcts_use_non_missing_bases(tiny_df: pd.DataFrame) -> None:
    derived = _derive_columns(tiny_df.copy())
    rec = volunteer_recruitment_analysis(derived)

    assert rec["n"] == len(tiny_df)
    assert 0 <= rec["pct_difficulty"] <= 100
    assert 0 <= rec["pct_shortage"] <= 100
    assert 0 <= rec["pct_too_few"] <= 100

    # In the tiny_df fixture, two of three organisations have shortage_vol_rec == Yes
    assert rec["pct_shortage"] == 66.7


def test_volunteer_retention_analysis_pcts_use_non_missing_bases(tiny_df: pd.DataFrame) -> None:
    derived = _derive_columns(tiny_df.copy())
    ret = volunteer_retention_analysis(derived)

    assert ret["n"] == len(tiny_df)
    assert 0 <= ret["pct_difficulty"] <= 100
    assert 0 <= ret["pct_shortage"] <= 100


def test_workforce_operations_headline_metrics(tiny_df: pd.DataFrame) -> None:
    derived = _derive_columns(tiny_df.copy())
    wf = workforce_operations(derived)

    assert wf["n"] == len(tiny_df)
    assert wf["n_with_staff"] == (tiny_df["paidworkforce"] == "Yes").sum()

    for key in [
        "staff_rec_difficulty_pct",
        "staff_ret_difficulty_pct",
        "vol_rec_difficulty_pct",
        "vol_ret_difficulty_pct",
        "finance_deteriorated_pct",
        "reserves_yes_pct",
        "using_reserves_pct",
    ]:
        assert 0 <= wf[key] <= 100


def test_finance_recruitment_cross_handles_small_samples() -> None:
    df_small = pd.DataFrame(
        {
            "financial_direction": ["Deteriorated"] * 3,
            "vol_rec": ["Somewhat difficult"] * 3,
        }
    )

    # Below minimum n=10 threshold, returns None
    assert finance_recruitment_cross(df_small) is None

