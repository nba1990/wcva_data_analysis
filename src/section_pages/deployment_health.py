# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""Deployment Health page: runtime asset checks and deployment readiness summary."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_deployment_health(
    asset_report: dict[str, Any],
    df_full: pd.DataFrame | None = None,
) -> None:
    """Render deployment/runtime health checks for the app environment.

    Args:
        asset_report: Output from data_loader.check_runtime_assets().
        df_full: Optional loaded dataset; if provided, basic shape info is shown.
    """
    st.title("Deployment Health")
    st.caption(
        "Quick runtime checks for the deployed app environment, expected files, "
        "and the currently loaded dataset."
    )

    all_required = asset_report["all_required_present"]
    required = pd.DataFrame(asset_report["required"])
    optional = pd.DataFrame(asset_report["optional"])
    dataset_source = asset_report.get("dataset_source")
    la_context_source = asset_report.get("la_context_source")
    app_mode = asset_report.get("app_mode", "real")

    top = st.columns(3)
    top[0].metric("App mode", "Demo" if app_mode == "demo" else "Real data")
    top[1].metric("Missing required", len(asset_report["missing_required"]))
    top[2].metric("Missing optional", len(asset_report["missing_optional"]))

    if app_mode == "demo":
        st.warning(
            "The app is running in demo mode from the bundled sample dataset. "
            "This is useful for smoke testing and docs builds, but not for real analysis."
        )
    elif all_required:
        st.success("Required runtime files are present.")
    else:
        st.error(
            "Some required runtime files are missing. The app may fail to start or "
            "behave incorrectly until these are restored."
        )
        for label in asset_report["missing_required"]:
            st.write(f"- {label}")

    if df_full is not None:
        st.subheader("Loaded Dataset")
        cols = st.columns(3)
        cols[0].metric("Rows", len(df_full))
        cols[1].metric("Columns", len(df_full.columns))
        cols[2].metric("Derived region column", "Yes" if "region" in df_full else "No")

    if dataset_source is not None or la_context_source is not None:
        st.subheader("Resolved Runtime Sources")
        source_rows = []
        if dataset_source is not None:
            source_rows.append(
                {
                    "source": "Wave dataset",
                    "mode": "demo" if dataset_source.is_demo else "real",
                    "type": dataset_source.source_type,
                    "value": dataset_source.value,
                }
            )
        if la_context_source is not None:
            source_rows.append(
                {
                    "source": "Local-authority context",
                    "mode": "public/override",
                    "type": la_context_source.source_type,
                    "value": la_context_source.value,
                }
            )
        st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)

    if dataset_source is not None:
        with st.expander("Dataset source resolution attempts"):
            for item in dataset_source.attempted:
                st.write(f"- {item}")

    if la_context_source is not None:
        with st.expander("Local-authority context resolution attempts"):
            for item in la_context_source.attempted:
                st.write(f"- {item}")

    st.subheader("Required Files")
    required_view = required.assign(
        status=required["exists"].map(lambda ok: "OK" if ok else "Missing")
    )[["label", "status", "path", "source_type", "mode"]]
    st.dataframe(required_view, width="stretch", hide_index=True)

    st.subheader("Optional Files")
    optional_view = optional.assign(
        status=optional["exists"].map(lambda ok: "OK" if ok else "Missing")
    )[["label", "status", "path", "source_type"]]
    st.dataframe(optional_view, width="stretch", hide_index=True)

    with st.expander("What to check in Streamlit Community Cloud"):
        st.markdown(
            "- Main file should be `src/app.py`.\n"
            "- Python version should be 3.11 or 3.12.\n"
            "- `requirements.txt` must contain all runtime dependencies.\n"
            "- Configure the private dataset via `dataset_path` / `dataset_url` in Secrets Manager, or the matching `WCVA_*` environment variables.\n"
            "- If the real dataset is unavailable, the app falls back to the sample fixture and marks the session as demo mode.\n"
            "- Secrets should be configured in Streamlit Secrets Manager, not in the repo."
        )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
