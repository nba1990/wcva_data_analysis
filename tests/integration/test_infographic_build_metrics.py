from __future__ import annotations

from src.infographic import _build_metrics


def test_build_metrics_trend_and_severity_with_previous_wave() -> None:
    dem = {
        "demand_pct_increased": 62.2,
        "demand_pct_increased_prev": 56.0,
        "financial_pct_deteriorated": 35.1,
        "financial_pct_deteriorated_prev": 74.0,
    }
    rec = {
        "pct_too_few": 63.6,
        "pct_too_few_prev": 55.0,
        "pct_difficulty": 53.3,
        "pct_difficulty_prev": 48.0,
    }
    ret = {
        "pct_difficulty": 34.3,
        "pct_difficulty_prev": 31.0,
    }

    metrics = _build_metrics(111, dem, rec, ret)

    demand = next(m for m in metrics if m["id"] == "demand")
    finance = next(m for m in metrics if m["id"] == "finance")
    too_few = next(m for m in metrics if m["id"] == "too_few")

    # Demand risk metric: higher share reporting increased demand is concerning.
    assert demand["trend_symbol"] in {"▲", "▼", "●"}
    assert demand["severity"] in {"positive", "mixed", "concerning"}

    # When a numeric previous is supplied (e.g. a future wave with same metric),
    # severity is still classified. (In the app we pass None for finance_prev
    # because Wave 1 only has the rising-costs measure, not the last-3-mth one.)
    assert finance["severity"] in {"positive", "mixed", "concerning"}

    # Too few volunteers at 63.6% should be classified at least as mixed / concerning.
    assert too_few["severity"] in {"mixed", "concerning"}


def test_build_metrics_finance_card_no_comparable_prev() -> None:
    """When financial_pct_deteriorated_prev is None (e.g. Wave 1 has no same measure),
    finance card shows neutral trend and 'No comparable' message instead of mixing metrics.
    """
    dem = {
        "demand_pct_increased": 62.2,
        "demand_pct_increased_prev": 56.0,
        "financial_pct_deteriorated": 35.1,
        "financial_pct_deteriorated_prev": None,
    }
    rec = {"pct_too_few": 63.6, "pct_difficulty": 53.3}
    ret = {"pct_difficulty": 34.3}

    metrics = _build_metrics(111, dem, rec, ret)
    finance = next(m for m in metrics if m["id"] == "finance")

    assert finance["trend_symbol"] == "●"
    assert finance["trend_class"] == "wcva-trend-neutral"
    assert "No comparable" in (finance.get("trend_vs_wave") or "")

