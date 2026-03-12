from __future__ import annotations

import pytest

from src.infographic import render_at_a_glance_infographic


@pytest.mark.e2e
def test_render_at_a_glance_infographic_smoke(monkeypatch) -> None:
    """
    Smoke test: ensure the infographic render function can be called without
    raising errors for a minimal set of metrics.

    The underlying Streamlit components.html call is monkeypatched so that
    no actual UI is launched during tests.
    """
    # Avoid calling real Streamlit during tests
    import src.infographic as infographic_module

    calls: list[dict] = []

    def fake_html(html: str, height: int = 0, **kwargs) -> None:  # type: ignore[override]
        calls.append({"html": html, "height": height, "kwargs": kwargs})

    monkeypatch.setattr(infographic_module.components, "html", fake_html)

    dem = {
        "demand_pct_increased": 60.0,
        "financial_pct_deteriorated": 40.0,
    }
    rec = {
        "pct_too_few": 63.6,
        "pct_difficulty": 53.3,
    }
    ret = {
        "pct_difficulty": 34.3,
    }

    render_at_a_glance_infographic(
        111,
        dem,
        rec,
        ret,
        height=600,
        accessible=False,
    )

    assert calls
    assert (
        "State of Volunteering" not in calls[0]["html"] or "<style>" in calls[0]["html"]
    )
