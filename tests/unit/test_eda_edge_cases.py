from __future__ import annotations

import pandas as pd

from src.data_loader import _derive_columns
from src.eda import (
    cross_segment_analysis,
    demand_and_outlook,
    finance_recruitment_cross,
    volunteer_demographics,
    volunteer_recruitment_analysis,
    volunteer_retention_analysis,
    volunteering_types,
    workforce_operations,
)


def test_eda_handles_empty_dataframe() -> None:
    df = pd.DataFrame(
        columns=[
            "demand",
            "financial",
            "operating",
            "workforce",
            "expectdemand",
            "expectfinancial",
            "location_la_primary",
            "shortage_staff_rec",
            "shortage_staff_ret",
            "paidworkforce",
            "reserves",
            "usingreserves",
            "monthsreserves",
            "shortage_vol_rec",
            "shortage_vol_ret",
            "vol_rec",
            "vol_ret",
            "org_size",
            "volobjectives",
            "financedeteriorate",
            "financial_direction",
        ]
    )
    derived = _derive_columns(df.copy())

    dem = demand_and_outlook(derived)
    rec = volunteer_recruitment_analysis(derived)
    ret = volunteer_retention_analysis(derived)
    wf = workforce_operations(derived)

    assert dem["demand_pct_increased"] == 0.0
    assert rec["pct_difficulty"] == 0
    assert ret["pct_difficulty"] == 0
    assert wf["n"] == 0


def test_volunteer_demographics_and_types_minimal() -> None:
    df = pd.DataFrame(
        {
            "vol_dem_1": [1],
            "vol_dem_change_1": ["Increased a lot"],
            "vol_time": ["Increased a little"],
            "earnedsettlement": ["Strongly agree"],
            "settlement_capacity": ["Already able to support"],
            "vol_typeuse_1": ["Featured heavily"],
        }
    )

    dem = volunteer_demographics(df)
    vt = volunteering_types(df)

    assert dem["n"] == 1
    assert not dem["dem_presence"].empty
    assert vt["n"] == 1
    assert vt["type_data"]


def test_cross_segment_analysis_min_n_threshold() -> None:
    df = pd.DataFrame(
        {
            "org_size": ["Small", "Small", "Small", "Medium"],
            "demand": ["Increased a lot"] * 4,
            "financial": ["Deteriorated a little"] * 4,
            "shortage_staff_rec": ["Yes"] * 4,
            "shortage_staff_ret": ["No"] * 4,
            "shortage_vol_rec": ["Yes"] * 4,
            "shortage_vol_ret": ["No"] * 4,
            "volobjectives": ["Slightly too few volunteers"] * 4,
            "location_la_primary": ["Cardiff"] * 4,
            "financedeteriorate": ["Yes"] * 4,
        }
    )
    derived = _derive_columns(df.copy())

    seg = cross_segment_analysis(derived)
    # Only Small should meet min_n=3; Medium (n=1) should be dropped
    sizes = seg["Organisation Size"]
    assert "Small" in sizes
    assert "Medium" not in sizes


def test_finance_recruitment_cross_positive_case() -> None:
    # Construct a small dataset that satisfies n>=10 and at least 3 in each group
    df = pd.DataFrame(
        {
            "financial_direction": (
                ["Deteriorated"] * 6  # 6 deteriorated
                + ["Stayed the same"] * 5  # 5 not deteriorated
            ),
            "vol_rec": (
                ["Somewhat difficult"] * 3
                + ["Extremely difficult"] * 3
                + ["Somewhat difficult"] * 2
                + ["Neither easy nor difficult"] * 3
            ),
        }
    )

    result = finance_recruitment_cross(df)
    assert result is not None
    assert result["n_finance_deteriorated"] == 6
    assert result["n_finance_not_deteriorated"] == 5
    assert 0 <= result["pct_rec_difficulty_if_finance_deteriorated"] <= 100
    assert 0 <= result["pct_rec_difficulty_if_finance_not_deteriorated"] <= 100


def test_finance_recruitment_cross_returns_none_when_insufficient_data() -> None:
    """When fewer than 3 in either finance group, cross-analysis returns None."""
    df = pd.DataFrame(
        {
            "financial_direction": ["Deteriorated", "Stayed the same"],
            "vol_rec": ["Somewhat difficult", "Neither easy nor difficult"],
        }
    )
    assert finance_recruitment_cross(df) is None
