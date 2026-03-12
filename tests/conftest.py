from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = (
    PROJECT_ROOT / "legacy_project_root"
)


# Ensure the Task root (parent of `src`) is on sys.path as soon as tests
# are imported. This allows `import src.*` in test modules during collection.
import sys  # noqa: E402

task_str = str(TASK_ROOT)
if task_str not in sys.path:
    sys.path.insert(0, task_str)


@pytest.fixture(scope="session", autouse=True)
def _ensure_src_on_path() -> None:
    """Session fixture kept for clarity; path is already set at import time."""
    return None


@pytest.fixture
def tiny_df() -> pd.DataFrame:
    """
    Minimal representative DataFrame used in several unit tests.
    """
    data = {
        "org_size": ["Small", "Medium", "Large"],
        "legalform": ["Charity", "CIC", "Charity"],
        "wales_scope": ["All Wales", "All Wales", "Local"],
        "mainactivity": ["Advice", "Environment", "Advice"],
        "location_la_primary": ["Cardiff", "Cardiff", "Swansea"],
        "demand": ["Increased a lot", "Stayed the same", "Decreased a little"],
        "financial": ["Deteriorated a little", "Stayed the same", "Improved a little"],
        "operating": ["Very likely", "Quite likely", "Quite unlikely"],
        "expectdemand": ["Increase a lot", "Stay the same", "Decrease a little"],
        "expectfinancial": [
            "Deteriorate a little",
            "Stay the same",
            "Improve a little",
        ],
        "workforce": ["Increased a lot", "Stayed the same", "Decreased a little"],
        "volobjectives": [
            "Slightly too few volunteers",
            "About the right number of volunteers",
            "Significantly too few volunteers",
        ],
        "shortage_vol_rec": ["Yes", "No", "Yes"],
        "shortage_vol_ret": ["No", "No", "Yes"],
        "vol_rec": [
            "Somewhat difficult",
            "Neither easy nor difficult",
            "Extremely difficult",
        ],
        "vol_ret": [
            "Somewhat difficult",
            "Somewhat easy",
            "Neither easy nor difficult",
        ],
        "paidworkforce": ["Yes", "No", "Yes"],
        "shortage_staff_rec": ["Yes", "No", "No"],
        "shortage_staff_ret": ["No", "No", "Yes"],
        "financedeteriorate": ["Yes", "No", "Yes"],
        "reserves": ["Yes", "Yes", "No"],
        "usingreserves": ["Yes", "No", "No"],
        "monthsreserves": [6, 3, 0],
        "peopleemploy": [5, 0, 12],
        "peoplevol": [20, 0, 5],
        "earnedsettlement": [
            "Strongly agree",
            "Neither agree nor disagree",
            "Somewhat disagree",
        ],
        "settlement_capacity": [
            "Would need additional funding",
            "Already able to support",
            "Not able to support",
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def la_context_csv(tmp_path: Path) -> Iterator[Path]:
    """
    Temporary local-authority context CSV mirroring the minimal columns used in data_loader/eda.
    """
    csv_path = tmp_path / "la_context_wales.csv"
    df = pd.DataFrame(
        {
            "local_authority": ["Cardiff", "Swansea"],
            "population_2024": [365000, 246000],
            "est_vcse_orgs": [2000, 1200],
        }
    )
    df.to_csv(csv_path, index=False)
    yield csv_path
