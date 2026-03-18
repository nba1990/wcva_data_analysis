from __future__ import annotations

from typing import Any

import pandas as pd
import pytest
import streamlit as st

from src.app import K_ANON_THRESHOLD
from src.data_loader import _derive_columns
from src.section_pages import executive_summary


@pytest.mark.integration
def test_executive_summary_respects_k_anonymity(monkeypatch: Any) -> None:
    """
    End-to-end style check: when the filtered sample falls below the
    k-anonymity threshold, the Executive Summary page should show a
    suppression warning and stop rendering charts/tables.
    """
    # Minimal tiny dataset that will be below K_ANON_THRESHOLD once filtered.
    # It must still include the core columns expected by _derive_columns.
    df = pd.DataFrame(
        {
            "location_la_primary": ["Cardiff"] * (K_ANON_THRESHOLD - 1),
            "demand": ["Increased a lot"] * (K_ANON_THRESHOLD - 1),
            "financial": ["Stayed the same"] * (K_ANON_THRESHOLD - 1),
            "shortage_vol_rec": ["No"] * (K_ANON_THRESHOLD - 1),
            "shortage_vol_ret": ["No"] * (K_ANON_THRESHOLD - 1),
            "shortage_staff_rec": ["No"] * (K_ANON_THRESHOLD - 1),
            "shortage_staff_ret": ["No"] * (K_ANON_THRESHOLD - 1),
            "financedeteriorate": ["No"] * (K_ANON_THRESHOLD - 1),
        }
    )
    derived = _derive_columns(df.copy())

    # Monkeypatch Streamlit's warning and stop to observe behaviour
    warnings: list[str] = []
    monkeypatch.setattr(st, "warning", lambda msg: warnings.append(str(msg)))

    stopped = {"called": False}

    class StopCalled(RuntimeError):
        """Sentinel exception to emulate Streamlit's stop behaviour."""

    def fake_stop() -> None:
        stopped["called"] = True
        raise StopCalled()

    monkeypatch.setattr(st, "stop", fake_stop)

    # Call the page renderer with suppressed=True; this should cause a
    # warning and an early stop before any detailed EDA runs.
    with pytest.raises(StopCalled):
        executive_summary.render_executive_summary(derived, suppressed=True)

    assert stopped["called"] is True
    assert any("suppressed" in msg.lower() for msg in warnings)
