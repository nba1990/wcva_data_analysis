"""
WCVA-branded Plotly chart generators.

Every function accepts a ``mode`` parameter ("brand" | "accessible")
that controls the colour palette.  All charts include:
  - redundant text labels (never colour-only encoding)
  - base size (n=) in the subtitle
  - alt-text metadata stored on the figure object
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    AltTextConfig, LabelGrouper, get_palette, get_likert_colours,
    WCVA_BRAND, CHART_FONT, CHART_FONT_SIZE, CHART_TITLE_SIZE,
    CHART_BG, CHART_GRID, CHART_MARGIN, make_stacked_bar_alt,
)


def _base_layout(title: str, n: int, height: int = 450, width: int | None = None) -> dict:
    """Shared layout defaults."""
    layout = dict(
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:12px;color:#666'>n = {n} organisations</span>",
            font=dict(family=CHART_FONT, size=CHART_TITLE_SIZE),
            x=0,
            xanchor="left",
        ),
        font=dict(family=CHART_FONT, size=CHART_FONT_SIZE, color=WCVA_BRAND["navy"]),
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
    """Attach alt-text metadata to a figure for accessibility."""
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
    """Horizontal bar chart ranked by value, with labels on bars."""
    data = df.head(max_items).copy()
    if exclude_na:
        data = data[~data[label_col].str.contains("N/A", case=False, na=False)]

    palette = get_palette(mode)
    colour = palette[0]

    text_vals = [f"{row[value_col]}  ({row[pct_col]}%)" for _, row in data.iterrows()] if pct_col else [str(v) for v in data[value_col]]

    fig = go.Figure(go.Bar(
        y=data[label_col],
        x=data[value_col],
        orientation="h",
        text=text_vals,
        textposition="outside",
        textfont=dict(size=12),
        marker_color=colour,
        cliponaxis=False,
    ))

    fig.update_layout(**_base_layout(title, n, height=max(height, len(data) * 36 + 100)))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=12))
    fig.update_xaxes(showgrid=True, gridcolor=CHART_GRID, zeroline=False, showticklabels=False)

    alt = f"Bar chart: {title}. Top item: {data.iloc[0][label_col]} ({data.iloc[0][value_col]}). Based on {n} organisations."
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
    """Single stacked horizontal bar showing Likert-scale distribution."""
    colours = get_likert_colours(mode)
    fig = go.Figure()

    for i, (_, row) in enumerate(df.iterrows()):
        colour = colours[i % len(colours)]
        label = row[alt_config.value_col]
        count = row[alt_config.count_col]
        pct = row[alt_config.pct_col]
        fig.add_trace(go.Bar(
            y=[""],
            x=[pct],
            orientation="h",
            name=label,
            text=f"{label}: {pct}%" if pct >= 5 else "",
            textposition="inside",
            textfont=dict(size=11, color="white" if i not in (2,) else WCVA_BRAND["navy"]),
            marker_color=colour,
            hovertemplate=f"{label}: {count} ({pct}%)<extra></extra>",
        ))

    base = _base_layout(title, n, height=height)
    base["showlegend"] = True
    fig.update_layout(
        **base,
        barmode="stack",
        legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="left", x=0, font=dict(size=11)),
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
    """Donut chart showing distribution based on sizes."""
    palette = get_palette(mode)
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=12),
        marker=dict(colors=palette[:len(labels)]),
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))

    fig.update_layout(**_base_layout(title, n, height=height))
    fig.update_layout(showlegend=False)

    # Sort by values in descending order
    org_sizes = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
    alt = f"Donut chart: {title}. Descending Order: {org_sizes}. n={n}."  # noqa
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
    """Grouped horizontal bars comparing segments (e.g. org sizes)."""
    data = df.head(max_items)
    palette = get_palette(mode)
    fig = go.Figure()

    for i, seg in enumerate(segment_cols):
        fig.add_trace(go.Bar(
            y=data[label_col],
            x=data[seg],
            orientation="h",
            name=seg,
            text=[f"{v}%" for v in data[seg]],
            textposition="outside",
            textfont=dict(size=10),
            marker_color=palette[i % len(palette)],
            cliponaxis=False,
        ))

    # _base_layout() already returns showlegend=False, and then grouped_bar() passes showlegend=True again
    #  - in the same update_layout() call. Passing Plotly two values for the same keyword argument.
    
    # fig.update_layout(
    #     **_base_layout(title, n, height=max(height, len(data) * 50 + 120)),
    #     barmode="group",
    #     showlegend=True,
    #     legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0),
    # )
    
    base = _base_layout(title, n, height=max(height, len(data) * 50 + 120))
    base["showlegend"] = True

    fig.update_layout(
        **base,
        barmode="group",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0),
    )

    fig.update_yaxes(autorange="reversed", tickfont=dict(size=11))
    fig.update_xaxes(showgrid=True, gridcolor=CHART_GRID, showticklabels=False)

    alt = f"Grouped bar: {title}, comparing {', '.join(segment_cols)}. n={n}."
    return _set_alt_text(fig, alt)


# ---------------------------------------------------------------------------
# 5. Heatmap matrix
# ---------------------------------------------------------------------------

# def heatmap_matrix(
#     df: pd.DataFrame,
#     row_col: str,
#     value_cols: list[str],
#     title: str,
#     n: int,
#     mode: str = "brand",
#     height: int = 500,
# ) -> go.Figure:
#     """Heatmap for demographic change matrix."""
#     z = df[value_cols].values
#     palette = get_palette(mode)

#     fig = go.Figure(go.Heatmap(
#         z=z,
#         x=value_cols,
#         y=df[row_col].tolist(),
#         text=z.astype(str),
#         texttemplate="%{text}",
#         textfont=dict(size=11),
#         colorscale=[
#             [0, palette[0]],
#             [0.5, "#F0F2F5"],
#             [1, palette[1]],
#         ],
#         showscale=True,
#         hovertemplate="Group: %{y}<br>Change: %{x}<br>Count: %{z}<extra></extra>",
#     ))

#     fig.update_layout(
#         **_base_layout(title, n, height=height),
#         xaxis=dict(tickfont=dict(size=10), tickangle=-30),
#         yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
#     )

#     alt = f"Heatmap: {title}. Shows counts across {len(value_cols)} change categories for {len(df)} groups. n={n}."
#     return _set_alt_text(fig, alt)

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
        collapsed["Increased"] = counts[increased_cols].sum(axis=1) if increased_cols else 0
        collapsed["Stayed the same"] = counts[same_cols].sum(axis=1) if same_cols else 0
        collapsed["Decreased"] = counts[decreased_cols].sum(axis=1) if decreased_cols else 0

        plot_counts = collapsed
        x_labels = ["Increased", "Stayed the same", "Decreased"]
    else:
        plot_counts = counts.copy()
        x_labels = value_cols

    row_totals = plot_counts.sum(axis=1)

    # Silent dtype downcasting during operations like .fillna() is being removed in future versions of pandas.
    # In future, pandas will not automatically convert object arrays back to numeric types and this needs to be handled explicitly.
    pct = (
        plot_counts
        .div(row_totals.replace(0, pd.NA), axis=0)
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
            f"{label} (n={int(base)})"
            for label, base in zip(labels, row_totals)
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

    customdata = [
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

    fig = go.Figure(go.Heatmap(
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
            ticksuffix="%"
        ),
        customdata=customdata,
        hovertemplate=(
            "Group: %{y}<br>"
            "Change: %{x}<br>"
            "Percentage: %{z:.1f}%<br>"
            "Count: %{customdata[0]}<br>"
            "Row base: %{customdata[2]}<extra></extra>"
        ),
    ))

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
    """Generate HTML for a single KPI metric card."""
    c = colour or WCVA_BRAND["navy"]
    delta_html = f"<div style='font-size:14px;color:#666;margin-top:2px'>{delta}</div>" if delta else ""
    return f"""
    <div style='background:#F7F8FA;border-left:4px solid {c};
                padding:16px 20px;border-radius:6px;min-width:140px'>
        <div style='font-size:14px;color:#666;margin-bottom:4px'>{label}</div>
        <div style='font-size:28px;font-weight:700;color:{c}'>{value}</div>
        {delta_html}
    </div>"""
