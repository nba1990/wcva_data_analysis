# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""Deployment Health page: runtime asset checks and deployment readiness summary."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from src.config import MAX_ROWS_STREAMLIT_UI, display_runtime_source, mask_runtime_value
from src.page_context import PageContext


def render_page(ctx: PageContext) -> None:
    """Standard section-page entrypoint used by src.app."""
    render_deployment_health(ctx.asset_report, ctx.df_full)


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

    # Simple session-level counters (reset on app reload) for how often
    # demo vs real modes have been used.
    demo_count_key = "deployment_health_demo_sessions"
    real_count_key = "deployment_health_real_sessions"
    if demo_count_key not in st.session_state:
        st.session_state[demo_count_key] = 0
    if real_count_key not in st.session_state:
        st.session_state[real_count_key] = 0
    if app_mode == "demo":
        st.session_state[demo_count_key] += 1
    else:
        st.session_state[real_count_key] += 1

    top = st.columns(4)
    top[0].metric("App mode", "Demo" if app_mode == "demo" else "Real data")
    top[1].metric("Missing required", len(asset_report["missing_required"]))
    top[2].metric("Missing optional", len(asset_report["missing_optional"]))
    top[3].metric(
        "Sessions (real / demo)",
        f"{st.session_state[real_count_key]} / {st.session_state[demo_count_key]}",
    )

    if app_mode == "demo":
        st.warning(
            "The app is running in demo mode from the bundled sample dataset. "
            "This is useful for smoke testing and docs builds, but not "
            "for real analysis."
        )
    elif all_required:
        st.success("Required runtime files are present.")
    else:
        st.error(
            "Some required runtime files are missing. The app may fail to "
            "start or behave incorrectly until these are restored."
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
                    "value": display_runtime_source(dataset_source),
                }
            )
        if la_context_source is not None:
            source_rows.append(
                {
                    "source": "Local-authority context",
                    "mode": "public/override",
                    "type": la_context_source.source_type,
                    "value": display_runtime_source(la_context_source),
                }
            )
        st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)

    if dataset_source is not None:
        with st.expander("Dataset source resolution attempts"):
            for item in dataset_source.attempted:
                st.write(f"- {mask_runtime_value(item)}")

    if la_context_source is not None:
        with st.expander("Local-authority context resolution attempts"):
            for item in la_context_source.attempted:
                st.write(f"- {mask_runtime_value(item)}")

    st.subheader("Required Files")
    required_view = required.assign(
        status=required["exists"].map(lambda ok: "OK" if ok else "Missing"),
        path=required["path"].map(mask_runtime_value),
    )[["label", "status", "path", "source_type", "mode"]]
    max_rows = MAX_ROWS_STREAMLIT_UI
    display_required = required_view.head(max_rows)
    st.dataframe(display_required, width="stretch", hide_index=True)
    if len(required_view) > max_rows:
        st.caption(
            f"Showing first {max_rows} required assets. Download the full table as CSV for offline diagnostics."
        )
    st.download_button(
        "Download required assets CSV",
        data=required_view.to_csv(index=False).encode("utf-8"),
        file_name="deployment_required_assets.csv",
        mime="text/csv",
        key="download_required_assets_csv",
    )

    st.subheader("Optional Files")
    optional_view = optional.assign(
        status=optional["exists"].map(lambda ok: "OK" if ok else "Missing"),
        path=optional["path"].map(mask_runtime_value),
    )[["label", "status", "path", "source_type"]]
    display_optional = optional_view.head(max_rows)
    st.dataframe(display_optional, width="stretch", hide_index=True)
    if len(optional_view) > max_rows:
        st.caption(
            f"Showing first {max_rows} optional assets. Download the full table as CSV for offline diagnostics."
        )
    st.download_button(
        "Download optional assets CSV",
        data=optional_view.to_csv(index=False).encode("utf-8"),
        file_name="deployment_optional_assets.csv",
        mime="text/csv",
        key="download_optional_assets_csv",
    )

    # Optional diagnostics JSON export for offline debugging
    with st.expander("Download diagnostics JSON"):
        # Build a JSON-serialisable snapshot of the asset report and dataset.
        safe_asset_report: dict[str, Any] = {
            key: value
            for key, value in asset_report.items()
            if key not in {"dataset_source", "la_context_source"}
        }

        if dataset_source is not None:
            safe_asset_report["dataset_source"] = {
                "label": dataset_source.label,
                "value": display_runtime_source(dataset_source),
                "source_type": dataset_source.source_type,
                "is_url": dataset_source.is_url,
                "is_demo": dataset_source.is_demo,
                "exists": dataset_source.exists,
            }

        if la_context_source is not None:
            safe_asset_report["la_context_source"] = {
                "label": la_context_source.label,
                "value": display_runtime_source(la_context_source),
                "source_type": la_context_source.source_type,
                "is_url": la_context_source.is_url,
                "exists": la_context_source.exists,
            }

        diagnostics: dict[str, Any] = {"asset_report": safe_asset_report}

        if df_full is not None:
            diagnostics["dataset"] = {
                "rows": int(len(df_full)),
                "columns": list(map(str, df_full.columns)),
            }

        json_bytes = json.dumps(diagnostics, indent=2).encode("utf-8")
        st.download_button(
            "Download diagnostics.json",
            data=json_bytes,
            file_name="deployment_diagnostics.json",
            mime="application/json",
            key="download_deployment_diagnostics",
        )

    with st.expander("What to check in Streamlit Community Cloud"):
        st.markdown(
            "- Main file should be `src/app.py`.\n"
            "- Python version should be 3.11 or 3.12.\n"
            "- `requirements.txt` must contain all runtime dependencies.\n"
            "- Configure the private dataset via `dataset_path` / `dataset_url` in Secrets Manager, or the matching `WCVA_*` environment variables.\n"
            "- If the real dataset is unavailable, the app falls back to the sample fixture and marks the session as demo mode.\n"
            "- Secrets should be configured in Streamlit Secrets Manager, not in the repo.\n"
            "\n"
            "For a fuller checklist on private data, secrets, and demo mode, see "
            "`docs/learning/02_private_data_secrets_and_demo_mode.md`. For container "
            "and runtime hardening (including where to mount datasets and how to pass "
            "env vars), see `docs/DOCKER_AND_DEPLOYMENT.md`."
        )


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
