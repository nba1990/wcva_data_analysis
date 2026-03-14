from __future__ import annotations

from src.narratives import (
    _safe_pct,
    demand_finance_scissor_phrase,
    recruitment_vs_retention_phrase,
)


def test_safe_pct_valid_mapping() -> None:
    assert _safe_pct({"demand_pct_increased": 50.0}, "demand_pct_increased") == 50.0
    assert _safe_pct({"x": "42"}, "x") == 42.0
    assert _safe_pct({}, "missing") == 0.0


def test_safe_pct_attribute_error_fallback() -> None:
    """Object without .get returns 0 (AttributeError path)."""

    class NoGet:
        pass

    assert _safe_pct(NoGet(), "key") == 0.0


def test_safe_pct_type_error_fallback() -> None:
    """Non-numeric value returns 0 (TypeError/ValueError path)."""
    assert _safe_pct({"key": "not-a-number"}, "key") == 0.0


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

    # Recruitment much harder than retention (ratio >= 1.8)
    msg_rec_harder = recruitment_vs_retention_phrase(
        {"pct_difficulty": 90}, {"pct_difficulty": 45}
    )
    assert "more commonly reported as difficult than" in msg_rec_harder

    # Retention easier (ratio < 0.9)
    msg_ret_easier = recruitment_vs_retention_phrase(
        {"pct_difficulty": 30}, {"pct_difficulty": 50}
    )
    assert "somewhat easier than" in msg_ret_easier
