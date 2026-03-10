from __future__ import annotations

import pandas as pd

from src.charts import (
    horizontal_bar_ranked,
    stacked_bar_ordinal,
    donut_chart,
    grouped_bar,
    heatmap_matrix,
    kpi_card_html,
)
from src.config import AltTextConfig


def test_horizontal_bar_ranked_basic() -> None:
    df = pd.DataFrame(
        {
            "label": ["A", "B", "N/A - no answer"],
            "value": [10, 5, 1],
            "pct": [50.0, 25.0, 5.0],
        }
    )

    fig = horizontal_bar_ranked(
        df,
        label_col="label",
        value_col="value",
        title="Top items",
        n=20,
        mode="brand",
        pct_col="pct",
    )

    assert fig.data
    assert hasattr(fig, "_alt_text")
    assert "Top items" in fig._alt_text


def test_stacked_bar_ordinal_with_alt_text() -> None:
    df = pd.DataFrame(
        [
            {"value": "Increased a lot", "count": 10, "pct": 25.0},
            {"value": "Increased a little", "count": 15, "pct": 37.5},
            {"value": "Stayed the same", "count": 8, "pct": 20.0},
            {"value": "Decreased", "count": 7, "pct": 17.5},
        ]
    )
    config = AltTextConfig(
        value_col="value",
        count_col="count",
        pct_col="pct",
        sample_size=40,
    )

    fig = stacked_bar_ordinal(
        df,
        title="Change in demand",
        n=40,
        mode="accessible",
        alt_config=config,
        grouper=None,
        group_order=None,
    )

    assert fig.data
    assert len(fig.data) == len(df)
    assert hasattr(fig, "_alt_text")
    assert "Change in demand" in fig._alt_text


def test_donut_chart_basic() -> None:
    labels = ["Small", "Medium", "Large"]
    values = [10, 20, 30]

    fig = donut_chart(
        labels,
        values,
        title="Org sizes",
        n=60,
        mode="brand",
    )

    assert fig.data
    assert len(fig.data[0]["labels"]) == 3
    assert hasattr(fig, "_alt_text")
    assert "Org sizes" in fig._alt_text


def test_grouped_bar_basic() -> None:
    df = pd.DataFrame(
        {
            "label": ["Barrier 1", "Barrier 2"],
            "Small": [30.0, 20.0],
            "Large": [40.0, 10.0],
        }
    )
    fig = grouped_bar(
        df,
        label_col="label",
        segment_cols=["Small", "Large"],
        title="Barriers by size",
        n=50,
        mode="brand",
    )

    assert len(fig.data) == 2  # one trace per segment
    assert hasattr(fig, "_alt_text")
    assert "Barriers by size" in fig._alt_text


def test_heatmap_matrix_full_and_collapsed_views() -> None:
    df = pd.DataFrame(
        {
            "group": ["A", "B"],
            "Increased a lot": [5, 0],
            "Increased a little": [5, 5],
            "Stayed the same": [0, 5],
            "Decreased a little": [0, 5],
            "Decreased a lot": [0, 0],
        }
    )
    value_cols = [
        "Increased a lot",
        "Increased a little",
        "Stayed the same",
        "Decreased a little",
        "Decreased a lot",
    ]

    # Full view
    fig_full = heatmap_matrix(
        df,
        row_col="group",
        value_cols=value_cols,
        title="Change matrix",
        n=10,
        mode="brand",
        view="full",
        show_row_bases=True,
        decimals=1,
    )
    assert fig_full.data
    assert hasattr(fig_full, "_alt_text")
    assert "Change matrix" in fig_full._alt_text

    # Collapsed view
    fig_collapsed = heatmap_matrix(
        df,
        row_col="group",
        value_cols=value_cols,
        title="Change matrix",
        n=10,
        mode="accessible",
        view="collapsed",
        show_row_bases=False,
        decimals=0,
    )
    assert fig_collapsed.data
    assert hasattr(fig_collapsed, "_alt_text")


def test_kpi_card_html_renders_label_value_and_delta() -> None:
    html = kpi_card_html("Label", "42%", delta="of organisations", colour="#123456")
    assert "Label" in html
    assert "42%" in html
    assert "of organisations" in html
    assert "#123456" in html

