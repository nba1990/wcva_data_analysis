import pandas as pd

from src.data_loader import load_dataset
from src.eda import (
    demand_and_outlook,
    volunteer_recruitment_analysis,
    volunteer_retention_analysis,
    workforce_operations,
    volunteering_types,
    finance_recruitment_cross,
)


def test_wave2_headline_metrics_match_qa_expectations() -> None:
    """
    Sanity-check the main Wave 2 headline metrics against the QA log.

    These figures are used across the executive summary, infographic,
    and slide deck, so this test acts as a guard-rail against accidental
    changes in calculation logic or denominators.
    """
    df = load_dataset()
    dem = demand_and_outlook(df)
    rec = volunteer_recruitment_analysis(df)
    ret = volunteer_retention_analysis(df)
    wf = workforce_operations(df)
    vt = volunteering_types(df)
    cross = finance_recruitment_cross(df)

    # Core demand / finance story
    assert dem["demand_pct_increased"] == 62.2
    assert dem["financial_pct_deteriorated"] == 35.1
    assert dem["operating_pct_likely"] == 92.8

    # Volunteer gap and difficulty
    assert rec["pct_too_few"] == 63.6
    assert rec["pct_difficulty"] == 53.3
    assert ret["pct_difficulty"] == 34.3

    # Rising-costs deterioration and reserves
    assert wf["finance_deteriorated_pct"] == 65.8
    assert wf["reserves_yes_pct"] == 85.6

    # Earned settlement distribution (counts)
    es = vt["earned_settlement"]
    counts = dict(zip(es["value"], es["count"]))
    assert counts["Strongly agree"] == 25
    assert counts["Somewhat agree"] == 17
    assert counts["Neither agree nor disagree"] == 31
    assert counts["Somewhat disagree"] == 1
    assert counts["Strongly disagree"] == 13
    assert counts["Don't know / too early to say"] == 16

    # Cross between finance deterioration and recruitment difficulty
    assert cross is not None
    assert cross["pct_rec_difficulty_if_finance_deteriorated"] == 61.5
    assert cross["pct_rec_difficulty_if_finance_not_deteriorated"] == 48.5
    assert cross["n_finance_deteriorated"] == 39
    assert cross["n_finance_not_deteriorated"] == 72


