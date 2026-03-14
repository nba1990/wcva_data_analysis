from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import horizontal_bar_ranked, show_chart, stacked_bar_ordinal
from src.config import (
    EARNED_SETTLEMENT_ORDER,
    AltTextConfig,
    get_app_ui_config,
    resolve_grouping,
)
from src.eda import volunteering_types
from src.wave_context import get_wave_registry


def render_earned_settlement(df: pd.DataFrame, n: int) -> None:
    """Render the Earned Settlement page: agreement and capacity charts.

    Args:
        df: Filtered analysis DataFrame.
        n: Filtered row count (for chart subtitles).
    """
    """Render the Earned Settlement page, using the current filtered dataset."""
    st.title("Earned Settlement Policy")
    st.markdown(
        "The Home Office's *Earned Settlement* proposal considers whether volunteering could "
        "count towards the time migrants need to qualify for permanent UK residency."
    )

    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    vt = volunteering_types(df)
    registry = get_wave_registry(df)

    col1, col2 = st.columns(2)
    alt_config = AltTextConfig(
        value_col="value", count_col="count", pct_col="pct", sample_size=n
    )
    with col1:
        st.subheader("Sentiment")
        grouper, group_order = resolve_grouping(EARNED_SETTLEMENT_ORDER)
        TITLE = (
            "More agree than disagree. But a large neutral/unsure group still exists"
        )
        fig = stacked_bar_ordinal(
            vt["earned_settlement"],
            TITLE,
            n,
            mode=ui_config.palette_mode,
            height=220,
            alt_config=alt_config,
            grouper=grouper,
            group_order=group_order,
        )
        show_chart(fig, "es_sentiment", vt["earned_settlement"])

    with col2:
        st.subheader("Organisational Capacity")
        cap = vt["settlement_capacity"]
        cap_df = pd.DataFrame(cap.items(), columns=["Capacity", "Count"]).sort_values(
            "Count", ascending=False
        )
        fig = horizontal_bar_ranked(
            cap_df,
            "Capacity",
            "Count",
            "Most would need additional resources or guidance to support this",
            n,
            mode=ui_config.palette_mode,
            pct_col=None,
            height=350,
        )
        show_chart(fig, "es_capacity", cap_df)

    st.info(
        "**Policy implication**: Sentiment is cautiously positive, but implementation would "
        "require significant support both in resources and clear guidance. Without it, the "
        "policy risks becoming an unfunded mandate."
    )

    st.info(
        "All earned settlement statements on this page and in the executive summary are backed by the "
        "`earnedsettlement` Likert distribution and the `settlement_capacity` counts shown in the charts "
        "above, via the **Volunteering Types & Earned Settlement analysis** (`volunteering_types`)."
    )
