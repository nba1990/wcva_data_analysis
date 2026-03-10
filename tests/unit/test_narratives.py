from __future__ import annotations

from src.narratives import demand_finance_scissor_phrase, recruitment_vs_retention_phrase


def test_demand_finance_scissor_phrase_no_data() -> None:
    text = demand_finance_scissor_phrase({})
    assert "no clear overall shift" in text


def test_demand_finance_scissor_phrase_both_metrics() -> None:
    text = demand_finance_scissor_phrase(
        {"demand_pct_increased": 60, "financial_pct_deteriorated": 40}
    )
    assert "60.0% of organisations report increased demand" in text
    assert "40.0% report their finances have deteriorated" in text
    assert "scissor effect" in text


def test_recruitment_vs_retention_phrase_various_cases() -> None:
    # No data
    assert "limited comparable data" in recruitment_vs_retention_phrase({}, {})

    # Only recruitment
    msg_rec_only = recruitment_vs_retention_phrase({"pct_difficulty": 70}, {})
    assert "retention data is too sparse" in msg_rec_only

    # Balanced case
    msg_balanced = recruitment_vs_retention_phrase(
        {"pct_difficulty": 50}, {"pct_difficulty": 48}
    )
    assert "about as hard as" in msg_balanced

