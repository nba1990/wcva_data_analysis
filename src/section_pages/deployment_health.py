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

    top = st.columns(3)
    top[0].metric("Required assets ready", "Yes" if all_required else "No")
    top[1].metric("Missing required", len(asset_report["missing_required"]))
    top[2].metric("Missing optional", len(asset_report["missing_optional"]))

    if all_required:
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

    st.subheader("Required Files")
    required_view = required.assign(
        status=required["exists"].map(lambda ok: "OK" if ok else "Missing")
    )[["label", "status", "path"]]
    st.dataframe(required_view, width="stretch", hide_index=True)

    st.subheader("Optional Files")
    optional_view = optional.assign(
        status=optional["exists"].map(lambda ok: "OK" if ok else "Missing")
    )[["label", "status", "path"]]
    st.dataframe(optional_view, width="stretch", hide_index=True)

    with st.expander("What to check in Streamlit Community Cloud"):
        st.markdown(
            "- Main file should be `src/app.py`.\n"
            "- Python version should be 3.11 or 3.12.\n"
            "- `requirements.txt` must contain all runtime dependencies.\n"
            "- Required datasets should be committed or otherwise supplied to the app environment.\n"
            "- Secrets should be configured in Streamlit Secrets Manager, not in the repo."
        )
