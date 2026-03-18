from __future__ import annotations

import pandas as pd

from src.config import CONCERNS_LABELS, StreamlitAppUISharedConfigState


def apply_filters(
    df_full: pd.DataFrame, ui_config: StreamlitAppUISharedConfigState
) -> pd.DataFrame:
    """Return a filtered view of df_full based on the current ui_config.

    This pure helper mirrors the sidebar filter logic in src.app and makes it
    easier to test filter behaviour independently of Streamlit UI code.
    """
    df = df_full

    if ui_config.selected_size != "All":
        df = df[df["org_size"] == ui_config.selected_size]
    if ui_config.selected_scope != "All":
        df = df[df["wales_scope"] == ui_config.selected_scope]
    if ui_config.selected_la_scope != "All":
        df = df[df["location_la_primary"] == ui_config.selected_la_scope]
    if ui_config.selected_activity != "All":
        df = df[df["mainactivity"] == ui_config.selected_activity]

    if ui_config.selected_paid_staff == "Has paid staff":
        df = df[df["paidworkforce"] == "Yes"]
    elif ui_config.selected_paid_staff == "No paid staff":
        df = df[df["paidworkforce"] == "No"]

    if ui_config.selected_concerns:
        label_to_column = {v: k for k, v in CONCERNS_LABELS.items()}
        concern_columns = [
            label_to_column[label]
            for label in ui_config.selected_concerns
            if label in label_to_column
        ]
        if concern_columns:
            mask = pd.Series(False, index=df.index)
            for col in concern_columns:
                if col in df.columns:
                    mask = mask | df[col].notna()
            df = df[mask]

    return df
