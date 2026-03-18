# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
WCVA-branded Plotly chart generators for the Baromedr dashboard.

All chart functions accept a ``mode`` parameter ("brand" | "accessible") for
the colour palette. Charts include redundant text labels, n= in subtitle, and
_alt_text on the figure for accessibility. Use show_chart() to render with
dynamic text scaling from session config and optional data download.

Main functions:
- horizontal_bar_ranked: Ranked horizontal bars.
- stacked_bar_ordinal: Likert/ordinal stacked bars with optional grouper.
- donut_chart: Donut with labels and values.
- grouped_bar: Grouped (segmented) bars by category.
- heatmap_matrix: Heatmap with optional row bases and collapsed view.
- kpi_card_html: HTML snippet for KPI tile (label, value, delta, colour).
- show_chart: Display figure with scaling and optional CSV download.
- wave_trend_line: Line chart for wave-over-wave trend.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import (
    ACCESSIBILITY_DEBUG,
    CHART_BG,
    CHART_FONT,
    CHART_FONT_SIZE,
    CHART_GRID,
    CHART_TITLE_SIZE,
    WCVA_BRAND,
    WCVA_LOGGER,
    AltTextConfig,
    LabelGrouper,
    get_app_ui_config,
    get_likert_colours,
    get_palette,
    make_stacked_bar_alt,
    validate_palette_contrast,
)


def _base_layout(
    title: str, n: int, height: int = 450, width: int | None = None
) -> dict:
    """Build shared Plotly layout dict (title with n= subtitle, fonts, bg, margins)."""
    subtitle = f"<span style='font-size:12px;color:#666'>n = {n} organisations</span>"
    layout = dict(
        title=dict(
            text=f"<b>{title}</b><br>{subtitle}",
            font=dict(family=CHART_FONT, size=CHART_TITLE_SIZE),
            x=0,
            xanchor="left",
        ),
        font=dict(
            family=CHART_FONT,
            size=CHART_FONT_SIZE,
            color=WCVA_BRAND["navy"],
        ),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        height=height,
        margin=dict(l=20, r=20, t=80, b=40),
        showlegend=False,
    )
    if width:
        layout["width"] = width
    return layout


def _set_alt_text(fig: go.Figure, text: str) -> go.Figure:
    """Attach alt-text to figure for accessibility caption in show_chart."""
    fig._alt_text = text
    return fig


# ---------------------------------------------------------------------------
# 1. Horizontal bar (ranked)
# ---------------------------------------------------------------------------


def horizontal_bar_ranked(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    n: int,
    mode: str = "brand",
    pct_col: str | None = "pct",
    max_items: int = 12,
    height: int = 450,
    exclude_na: bool = True,
) -> go.Figure:
    """Build horizontal bar chart ranked by value_col, with text labels on bars.

    Args:
        df: DataFrame with label_col, value_col, and optionally pct_col.
        label_col: Column for bar labels (y-axis).
        value_col: Column for bar lengths (x-axis).
        title: Chart title (includes n= in layout).
        n: Sample size for subtitle.
        mode: "brand" or "accessible" palette.
        pct_col: If set, bar text shows value and pct.
        max_items: Max number of bars.
        height: Chart height in px.
        exclude_na: If True, drop rows where label contains "N/A".

    Returns:
        go.Figure with _alt_text set.
    """
    data = df.head(max_items).copy()
    if exclude_na:
        data = data[~data[label_col].str.contains("N/A", case=False, na=False)]

    palette = get_palette(mode)
    colour = palette[0]

    if pct_col:
        text_vals = [
            f"{row[value_col]}  ({row[pct_col]}%)" for _, row in data.iterrows()
        ]
    else:
        text_vals = [str(v) for v in data[value_col]]

    fig = go.Figure(
        go.Bar(
            y=data[label_col],
            x=data[value_col],
            orientation="h",
            text=text_vals,
            textposition="outside",
            textfont=dict(size=14),
            marker_color=colour,
            cliponaxis=False,
        )
    )

    fig.update_layout(
        **_base_layout(title, n, height=max(height, len(data) * 40 + 110))
    )
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=13))
    fig.update_xaxes(
        showgrid=True, gridcolor=CHART_GRID, zeroline=False, showticklabels=False
    )

    if data.empty:
        fig.add_annotation(
            text="No data available for this view",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color=WCVA_BRAND["mid_grey"]),
        )
        alt = f"Bar chart: {title}. No ranked items available for this view. Based on {n} organisations."
        return _set_alt_text(fig, alt)

    alt = (
        f"Bar chart: {title}. Top item: "
        f"{data.iloc[0][label_col]} ({data.iloc[0][value_col]}). "
        f"Based on {n} organisations."
    )
    return _set_alt_text(fig, alt)


# ---------------------------------------------------------------------------
# 2. Stacked bar (ordinal / Likert)
# ---------------------------------------------------------------------------


def stacked_bar_ordinal(
    df: pd.DataFrame,
    title: str,
    n: int,
    mode: str = "brand",
    height: int = 200,
    alt_config: AltTextConfig | None = None,
    grouper: LabelGrouper | None = None,
    group_order: list[str] | None = None,
) -> go.Figure:
    """Single stacked horizontal bar for Likert/ordinal distribution.

    Uses alt_config for value/count/pct columns and optional grouper for
    accessibility summary. Legend below chart; alt_text from make_stacked_bar_alt.

    Args:
        df: One row per category with value, count, pct (or alt_config columns).
        title: Chart title.
        n: Sample size for layout.
        mode: "brand" or "accessible" Likert colours.
        height: Chart height in px.
        alt_config: Required for alt-text; value_col, count_col, pct_col, sample_size.
        grouper: Optional label grouper for alt summary.
        group_order: Optional order for grouped alt summary.

    Returns:
        go.Figure with _alt_text set.
    """
    colours = get_likert_colours(mode)
    fig = go.Figure()

    for i, (_, row) in enumerate(df.iterrows()):
        colour = colours[i % len(colours)]
        label = row[alt_config.value_col]
        count = row[alt_config.count_col]
        pct = row[alt_config.pct_col]
        fig.add_trace(
            go.Bar(
                y=[""],
                x=[pct],
                orientation="h",
                name=label,
                text=f"{label}: {pct}%" if pct >= 4 else "",
                textposition="inside",
                textfont=dict(
                    size=12,
                    color="white" if i not in (2,) else WCVA_BRAND["navy"],
                ),
                marker_color=colour,
                hovertemplate=f"{label}: {count} ({pct}%)<extra></extra>",
            )
        )

    base = _base_layout(title, n, height=height)
    base["showlegend"] = True
    fig.update_layout(
        **base,
        barmode="stack",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.3,
            xanchor="left",
            x=0,
            font=dict(size=12),
        ),
    )
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, 100])
    fig.update_yaxes(showticklabels=False)
    ALT_TEXT = make_stacked_bar_alt(
        df=df,
        title=title,
        config=alt_config,
        grouper=grouper,
        group_order=group_order,
    )

    return _set_alt_text(fig, ALT_TEXT)


# ---------------------------------------------------------------------------
# 3. Donut chart
# ---------------------------------------------------------------------------


def donut_chart(
    labels: list[str],
    values: list[int],
    title: str,
    n: int,
    mode: str = "brand",
    height: int = 400,
) -> go.Figure:
    """Donut chart with labels, values, and n= in subtitle.

    Args:
        labels: Category names for each slice.
        values: Count or magnitude per slice.
        title: Chart title.
        n: Sample size for subtitle.
        mode: "brand" or "accessible" palette.
        height: Chart height in px.

    Returns:
        go.Figure with _alt_text set.
    """
    palette = get_palette(mode)
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(size=13),
            marker=dict(colors=palette[: len(labels)]),
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        )
    )

    fig.update_layout(**_base_layout(title, n, height=height))
    fig.update_layout(showlegend=False)

    # Sort by values in descending order
    org_sizes = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
    alt = f"Donut chart: {title}. Descending Order: {org_sizes}. n={n}."
    return _set_alt_text(fig, alt)


# ---------------------------------------------------------------------------
# 4. Grouped bar (segment comparison)
# ---------------------------------------------------------------------------


def grouped_bar(
    df: pd.DataFrame,
    label_col: str,
    segment_cols: list[str],
    title: str,
    n: int,
    mode: str = "brand",
    height: int = 500,
    max_items: int = 8,
) -> go.Figure:
    """Grouped horizontal bars: one trace per segment, comparing by label.

    Args:
        df: Rows = categories (label_col), columns include segment_cols (pct values).
        label_col: Row labels (y-axis).
        segment_cols: Column names for each segment (e.g. Small, Medium, Large).
        title: Chart title.
        n: Sample size.
        mode: "brand" or "accessible" palette.
        height: Chart height; auto-increased by row count.
        max_items: Max rows to show.

    Returns:
        go.Figure with _alt_text set.
    """
    data = df.head(max_items)
    palette = get_palette(mode)
    fig = go.Figure()

    for i, seg in enumerate(segment_cols):
        fig.add_trace(
            go.Bar(
                y=data[label_col],
                x=data[seg],
                orientation="h",
                name=seg,
                text=[f"{v}%" for v in data[seg]],
                textposition="outside",
                textfont=dict(size=11),
                marker_color=palette[i % len(palette)],
                cliponaxis=False,
            )
        )

    base = _base_layout(title, n, height=max(height, len(data) * 50 + 120))
    base["showlegend"] = True

    fig.update_layout(
        **base,
        barmode="group",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0),
    )

    fig.update_yaxes(autorange="reversed", tickfont=dict(size=12))
    fig.update_xaxes(showgrid=True, gridcolor=CHART_GRID, showticklabels=False)

    seg_list = ", ".join(segment_cols)
    alt = f"Grouped bar: {title}, comparing {seg_list}. n={n}."
    return _set_alt_text(fig, alt)


# ---------------------------------------------------------------------------
# 5. Heatmap matrix
# ---------------------------------------------------------------------------


def heatmap_matrix(
    df: pd.DataFrame,
    row_col: str,
    value_cols: list[str],
    title: str,
    n: int,
    mode: str = "brand",
    height: int = 500,
    view: str = "full",  # "full" | "collapsed"
    show_row_bases: bool = True,
    decimals: int = 0,
) -> go.Figure:
    """
    Heatmap showing row-wise percentage distribution, with counts in labels.

    Parameters
    ----------
    df : pd.DataFrame
        Source dataframe.
    row_col : str
        Column containing row labels.
    value_cols : list[str]
        Ordered response columns for the full view.
    title : str
        Chart title.
    n : int
        Overall survey base shown in subtitle.
    mode : str
        Colour mode passed to get_palette().
    height : int
        Figure height.
    view : str
        "full" for all original columns, or "collapsed" for
        Increased / Stayed the same / Decreased.
    show_row_bases : bool
        Whether to append row-specific bases to y-axis labels.
    decimals : int
        Decimal places for displayed percentages.
    """
    data = df.copy()
    counts = data[value_cols].fillna(0).astype(float)

    if view not in {"full", "collapsed"}:
        raise ValueError("view must be 'full' or 'collapsed'")

    if view == "collapsed":
        increased_candidates = ["Increased a lot", "Increased a little"]
        same_candidates = ["Stayed the same"]
        decreased_candidates = ["Decreased a little", "Decreased a lot"]

        increased_cols = [c for c in increased_candidates if c in counts.columns]
        same_cols = [c for c in same_candidates if c in counts.columns]
        decreased_cols = [c for c in decreased_candidates if c in counts.columns]

        collapsed = pd.DataFrame(index=data.index)
        collapsed["Increased"] = (
            counts[increased_cols].sum(axis=1) if increased_cols else 0
        )
        collapsed["Stayed the same"] = counts[same_cols].sum(axis=1) if same_cols else 0
        collapsed["Decreased"] = (
            counts[decreased_cols].sum(axis=1) if decreased_cols else 0
        )

        plot_counts = collapsed
        x_labels = ["Increased", "Stayed the same", "Decreased"]
    else:
        plot_counts = counts.copy()
        x_labels = value_cols

    row_totals = plot_counts.sum(axis=1)

    # Silent dtype downcasting during operations like .fillna() is being removed in future versions of pandas.
    # In future, pandas will not automatically convert object arrays back to numeric types and this needs to be handled explicitly.
    pct = (
        plot_counts.div(
            row_totals.replace(0, pd.NA),
            axis=0,
        )
        .fillna(0)
        .infer_objects(copy=False)
        * 100
    )

    # Determine row labels
    if row_col in data.columns:
        labels = data[row_col].tolist()
    elif data.index.name == row_col or row_col is None:
        labels = data.index.tolist()
    else:
        raise KeyError(f"'{row_col}' not found in dataframe columns or index")

    if show_row_bases:
        y_labels = [
            f"{label} (n={int(base)})" for label, base in zip(labels, row_totals)
        ]
    else:
        y_labels = labels

    text = [
        [
            f"{pct.iloc[i, j]:.{decimals}f}%\n({int(plot_counts.iloc[i, j])})"
            for j in range(len(x_labels))
        ]
        for i in range(len(data))
    ]

    custom_data = [
        [
            [
                int(plot_counts.iloc[i, j]),
                float(pct.iloc[i, j]),
                int(row_totals.iloc[i]),
            ]
            for j in range(len(x_labels))
        ]
        for i in range(len(data))
    ]

    palette = get_palette(mode)
    heat_colour = palette[0]
    colorscale = [
        [0.00, "#F7FAFC"],
        [0.20, "#DCEFEF"],
        [0.40, "#B8DDDD"],
        [0.60, "#7FC1C1"],
        [0.80, "#3E9E9E"],
        [1.00, heat_colour],
    ]

    fig = go.Figure(
        go.Heatmap(
            z=pct.values,
            x=x_labels,
            y=y_labels,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=11),
            colorscale=colorscale,
            zmin=0,
            zmax=100,
            showscale=True,
            colorbar=dict(
                title="% of row",
                tickmode="array",
                tickvals=[0, 25, 50, 75, 100],
                ticksuffix="%",
            ),
            customdata=custom_data,
            hovertemplate=(
                "Group: %{y}<br>"
                "Change: %{x}<br>"
                "Percentage: %{z:.1f}%<br>"
                "Count: %{custom_data[0]}<br>"
                "Row base: %{custom_data[2]}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        **_base_layout(title, n, height=height),
        xaxis=dict(
            tickfont=dict(size=10),
            tickangle=-25 if view == "full" else 0,
            side="bottom",
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            autorange="reversed",
        ),
    )

    alt = (
        f"Heatmap: {title}. "
        f"View={view}. "
        f"Colour shows row percentages across {len(x_labels)} change categories for {len(data)} groups. "
        f"Cell labels show percentage and count. "
        f"Overall survey base n={n}."
    )
    return _set_alt_text(fig, alt)


# ---------------------------------------------------------------------------
# 6. KPI metric card (for Streamlit)
# ---------------------------------------------------------------------------


def kpi_card_html(label: str, value: str, delta: str = "", colour: str = "") -> str:
    """Generate HTML for a single KPI metric card (label, value, optional delta, left border colour).

    Args:
        label: Card title (e.g. "Organisations reporting increased demand").
        value: Main value (e.g. "66.7%").
        delta: Optional second line (e.g. "vs 50% last wave").
        colour: Hex colour for value and left border; default WCVA navy.

    Returns:
        HTML string for st.markdown(..., unsafe_allow_html=True).
    """
    c = colour or WCVA_BRAND["navy"]
    delta_html = (
        f"<div style='font-size:14px;color:#666;margin-top:2px'>{delta}</div>"
        if delta
        else ""
    )
    return f"""
    <div style='background:#F7F8FA;border-left:4px solid {c};
                padding:16px 20px;border-radius:6px;min-width:140px'>
        <div style='font-size:14px;color:#666;margin-bottom:4px'>{label}</div>
        <div style='font-size:28px;font-weight:700;color:{c}'>{value}</div>
        {delta_html}
    </div>"""


# ---------------------------------------------------------------------------
# Helper: chart display with download
# ---------------------------------------------------------------------------


def show_chart(fig: go.Figure, key: str, data_df: pd.DataFrame | None = None) -> None:
    """Display a Plotly chart with optional download buttons and accessibility caption."""
    ui_config = get_app_ui_config()
    # Apply dynamic text scaling from sidebar control
    if ui_config.text_scale != 1.0:
        scale = ui_config.text_scale
        fig.update_layout(
            font=dict(size=CHART_FONT_SIZE * scale),
            title_font_size=CHART_TITLE_SIZE * scale,
            legend=dict(font=dict(size=CHART_FONT_SIZE * scale)),
        )
        fig.update_xaxes(tickfont_size=CHART_FONT_SIZE * scale)
        fig.update_yaxes(tickfont_size=CHART_FONT_SIZE * scale)

    # Optional accessibility diagnostics: when ACCESSIBILITY_DEBUG is enabled,
    # log alt-text and basic palette contrast information for a few charts to
    # make external accessibility review easier.
    if ACCESSIBILITY_DEBUG and hasattr(fig, "_alt_text"):
        try:
            palette_mode = getattr(ui_config, "palette_mode", "brand")
            palette = get_palette(palette_mode)
            contrast = validate_palette_contrast(palette)
            WCVA_LOGGER.info(
                "Accessibility debug",
                extra={
                    "chart_key": key,
                    "palette_mode": palette_mode,
                    "palette": palette,
                    "contrast_with_bg": contrast,
                    "alt_text": fig._alt_text,
                },
            )
        except Exception as exc:
            # Diagnostics must never break chart rendering.
            WCVA_LOGGER.debug("Accessibility diagnostics failed", exc_info=exc)

    st.plotly_chart(fig, width="stretch", key=key)
    if hasattr(fig, "_alt_text"):
        st.caption(f"Accessibility: {fig._alt_text}")

    if data_df is not None:
        with st.expander("View/download data table"):
            # st.dataframe(data_df, use_container_width=True)
            # use_container_width=True is deprecated and is already removed in Streamlit since 2025-12-31
            st.dataframe(data_df, width="stretch")
            csv = data_df.to_csv(index=False)
            st.download_button(
                "Download CSV", csv, f"{key}.csv", "text/csv", key=f"dl_{key}"
            )


def wave_trend_line(
    df: pd.DataFrame,
    title: str,
    *,
    value_col: str = "value",
    wave_number_col: str = "wave_number",
    wave_label_col: str = "wave_label",
    wave_n_col: str = "wave_n",
    mode: str = "brand",
) -> go.Figure:
    """
    Build a consistent line+marker chart for wave-based trends.

    This is used by multiple section pages to show how a percentage metric
    evolves across survey waves, and centralises colour, layout and alt-text.
    """
    data = df.sort_values(wave_number_col)
    palette = get_palette(mode)
    colour = palette[0]

    fig = go.Figure(
        go.Scatter(
            x=data[wave_number_col],
            y=data[value_col],
            mode="lines+markers+text",
            text=data[value_col],
            textposition="top center",
            marker=dict(color=colour, size=8),
            line=dict(color=colour, width=2),
        )
    )

    x_ticks = data[wave_number_col]
    x_labels = data[wave_label_col]

    fig.update_layout(
        title=dict(text=title, font=dict(family=CHART_FONT, size=CHART_TITLE_SIZE)),
        font=dict(family=CHART_FONT, size=CHART_FONT_SIZE, color=WCVA_BRAND["navy"]),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        height=360,
        margin=dict(l=40, r=20, t=70, b=60),
        showlegend=False,
        xaxis=dict(
            title="Wave",
            tickvals=x_ticks,
            ticktext=x_labels,
            gridcolor=CHART_GRID,
        ),
        yaxis=dict(title="Percent", gridcolor=CHART_GRID, rangemode="tozero"),
    )

    unique_waves = (
        data[[wave_label_col, wave_n_col]].drop_duplicates().sort_values(wave_label_col)
    )
    wave_summaries = ", ".join(
        f"{row[wave_label_col]} (n={row[wave_n_col]})"
        for _, row in unique_waves.iterrows()
    )
    n_waves = unique_waves.shape[0]
    alt = (
        f"Trend line for {title} across {n_waves} waves. "
        f"Waves and respondent counts: {wave_summaries}."
    )
    return _set_alt_text(fig, alt)


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
