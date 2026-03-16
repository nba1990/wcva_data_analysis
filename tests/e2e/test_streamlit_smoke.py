# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import src.eda as eda_module
import src.navigation as navigation_module
import src.section_pages.at_a_glance as at_a_glance_module
import src.section_pages.concerns_and_risks as concerns_module
import src.section_pages.data_notes as data_notes_module
import src.section_pages.demographics_and_types as demographics_module
import src.section_pages.deployment_health as deployment_health_module
import src.section_pages.earned_settlement as earned_settlement_module
import src.section_pages.executive_summary as executive_summary_module
import src.section_pages.overview as overview_module
import src.section_pages.sroi_references as sroi_module
import src.section_pages.trends_and_waves as trends_module
import src.section_pages.volunteer_recruitment as volunteer_recruitment_module
import src.section_pages.volunteer_retention as volunteer_retention_module
import src.section_pages.workforce_and_operations as workforce_module


@pytest.mark.e2e
def test_app_module_imports(monkeypatch) -> None:
    """
    Minimal smoke test: importing the Streamlit app module should succeed.

    This catches import-time errors (missing dependencies, bad relative
    imports, etc.) without starting a real Streamlit server, which can be
    flaky in headless CI environments.
    """
    project_root = Path(__file__).resolve().parents[2]
    la_context = project_root / "references" / "context" / "la_context_wales.csv"

    monkeypatch.delenv("WCVA_DATASET_PATH", raising=False)
    monkeypatch.delenv("WCVA_DATASET_URL", raising=False)
    monkeypatch.setenv("WCVA_LA_CONTEXT_PATH", str(la_context))
    monkeypatch.setattr(
        navigation_module,
        "render_sidebar_nav",
        lambda current_page=None: "Deployment Health",
    )
    monkeypatch.setattr(
        eda_module,
        "profile_summary",
        lambda df: {
            "has_volunteers_pct": 0.0,
            "has_paid_staff_pct": 0.0,
            "la_context": [],
        },
    )
    for module_name in [
        at_a_glance_module,
        concerns_module,
        data_notes_module,
        demographics_module,
        deployment_health_module,
        earned_settlement_module,
        executive_summary_module,
        overview_module,
        sroi_module,
        trends_module,
        volunteer_recruitment_module,
        volunteer_retention_module,
        workforce_module,
    ]:
        for attr_name in dir(module_name):
            if attr_name.startswith("render_"):
                monkeypatch.setattr(
                    module_name, attr_name, lambda *args, **kwargs: None
                )

    sys.modules.pop("src.app", None)

    __import__("src.app")


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
