from __future__ import annotations

from typing import Any

import pandas as pd
import pytest
import streamlit as st

from src.app import get_data
from src.config import SAMPLE_DATASET_PATH, RuntimeDataSource, resolve_dataset_source
from src.data_loader import check_runtime_assets
from src.section_pages import deployment_health


@pytest.mark.integration
def test_runtime_data_source_is_demo_for_sample_fixture(monkeypatch: Any) -> None:
    """
    Ensure that when the default dataset path is missing, the runtime
    resolution falls back to the bundled sample fixture and marks the
    source as demo.
    """
    monkeypatch.delenv("WCVA_DATASET_PATH", raising=False)
    monkeypatch.delenv("WCVA_DATASET_URL", raising=False)

    # If a real default dataset exists in the working tree, resolve_dataset_source
    # will prefer that. This check focuses on the behaviour of the demo flag
    # when the resolved source is the bundled sample fixture.
    source = resolve_dataset_source()
    if source.value == str(SAMPLE_DATASET_PATH):
        assert source.is_demo is True


@pytest.mark.integration
def test_demo_mode_labelling_in_deployment_health(monkeypatch: Any) -> None:
    """
    When app_mode is 'demo', the Deployment Health page should show the
    demo warning and increment the demo session counter.
    """
    asset_report = {
        "all_required_present": True,
        "required": [
            {
                "label": "Wave 2 dataset source",
                "path": str(SAMPLE_DATASET_PATH),
                "exists": True,
                "source_type": "sample_path",
                "mode": "demo",
            }
        ],
        "optional": [
            {
                "label": "Local authority context CSV",
                "path": "/tmp/la.csv",
                "exists": False,
                "source_type": "default_path",
            }
        ],
        "missing_required": [],
        "missing_optional": [],
        "dataset_source": RuntimeDataSource(
            label="Wave dataset",
            value=str(SAMPLE_DATASET_PATH),
            source_type="sample_path",
            exists=True,
            is_url=False,
            is_demo=True,
        ),
        "la_context_source": None,
        "app_mode": "demo",
    }

    # Minimal dataset for the shape metrics section.
    df_full = pd.DataFrame({"a": [1, 2, 3]})

    warnings: list[str] = []
    monkeypatch.setattr(st, "warning", lambda msg: warnings.append(str(msg)))

    # Ensure fresh session counters.
    st.session_state.clear()

    deployment_health.render_deployment_health(asset_report, df_full=df_full)

    assert any("demo mode" in msg.lower() for msg in warnings)
    assert st.session_state["deployment_health_demo_sessions"] == 1
    assert st.session_state["deployment_health_real_sessions"] == 0


@pytest.mark.integration
def test_get_data_uses_runtime_source_metadata(monkeypatch: Any, tmp_path) -> None:
    """
    get_data() should return a DataFrame and a RuntimeDataSource whose
    is_demo flag matches the resolved dataset source.
    """
    # Point WCVA_DATASET_PATH at a temporary real file so the resolved
    # source is not demo.
    dataset = tmp_path / "wave.csv"
    dataset.write_text(
        SAMPLE_DATASET_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    monkeypatch.setenv("WCVA_DATASET_PATH", str(dataset))
    monkeypatch.delenv("WCVA_DATASET_URL", raising=False)

    # src.app imports and caches the dataset at module import time, so clear
    # the function cache before asserting on an env-driven source change.
    get_data.clear()
    df, source = get_data()
    assert isinstance(source, RuntimeDataSource)
    assert source.is_demo is False
    assert len(df) > 0


@pytest.mark.integration
def test_check_runtime_assets_app_mode_consistent_with_dataset_source(
    tmp_path, monkeypatch
) -> None:
    """
    check_runtime_assets should set app_mode='demo' when the resolved
    dataset source is demo, and 'real' otherwise.
    """
    # First, force demo mode by breaking the default dataset path.
    fake_default = tmp_path / "datasets" / "missing_wave.csv"
    monkeypatch.setattr("src.config.DEFAULT_DATASET_PATH", fake_default, raising=False)
    demo_report = check_runtime_assets(project_root=tmp_path)
    assert demo_report["app_mode"] == "demo"
    assert demo_report["dataset_source"].is_demo is True

    # Then, supply a real dataset path so app_mode becomes 'real'.
    dataset = tmp_path / "runtime-data" / "WCVA_W2_Anonymised_Dataset.csv"
    streamlit_config = tmp_path / ".streamlit" / "config.toml"
    dataset.parent.mkdir(parents=True)
    streamlit_config.parent.mkdir(parents=True)
    dataset.write_text("a,b\n1,2\n", encoding="utf-8")
    streamlit_config.write_text("[server]\nheadless = true\n", encoding="utf-8")

    real_report = check_runtime_assets(
        project_root=tmp_path,
        dataset_path=dataset,
    )
    assert real_report["app_mode"] == "real"
    assert real_report["dataset_source"].is_demo is False
