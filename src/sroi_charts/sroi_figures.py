# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
SROI and reference chart factories for the SROI & References page.

Each make_*_figure returns a go.Figure with optional palette_mode and text_scale.
Charts: funding flows, SROI comparison, volunteering value, measurement gap,
WCVA/WG funding, NLCF Wales, alignment heatmap, framework flow, timeline.
"""

from __future__ import annotations

import plotly.graph_objects as go

from src.config import ACCESSIBLE_SEQUENCE, BRAND_SEQUENCE

SUBTITLE_FONT = 10
PLOT_BGCOLOUR = "rgb(229, 236, 246)"


def _scale_layout(fig: go.Figure, text_scale: float) -> None:
    """Apply text_scale multiplier to figure font and title sizes (in-place)."""
    base_size = 14
    title_size = 16
    fig.update_layout(
        font=dict(size=base_size * text_scale),
        title=dict(font=dict(size=title_size * text_scale)),
    )


def make_funding_flows_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    funding_sources = [
        "WG Direct Grants",
        "WG via WCVA",
        "NLCF Wales",
        "UK SPF Wales",
        "Comm. Facilities Prog. (~£7m)",
        "Other (Trusts, Corporate, etc.)",
    ]
    amounts = [668, 24.5, 39, 195, 7, 50]

    palette = ACCESSIBLE_SEQUENCE if palette_mode == "accessible" else BRAND_SEQUENCE

    fig = go.Figure(
        go.Bar(
            x=amounts,
            y=funding_sources,
            orientation="h",
            text=[f"£{v:.0f}m" if v >= 1 else f"£{v:.1f}m" for v in amounts],
            textposition="outside",
            marker_color=palette[: len(funding_sources)],
        )
    )
    fig.update_layout(
        title=dict(
            text="Est. Public Funding to Welsh Voluntary Sector (Annual)",
            subtitle=dict(
                text="Sources: FOI data, WG budgets, NLCF reports | ~2024 estimates",
                font=dict(size=SUBTITLE_FONT),
            ),
        ),
        xaxis_title="Amount (£m)",
        yaxis_title="",
        showlegend=False,
        height=500,
        width=900,
        plot_bgcolor=PLOT_BGCOLOUR,
    )
    fig.update_traces(cliponaxis=False)
    _scale_layout(fig, text_scale)
    return fig


def make_sroi_comparison_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    sroi_labels = [
        "Sport Wales (2021/22)",
        "Cyfle Cymru North Wales",
        "Vol. Gardening (Wales)",
        "Citizens Advice on Prescription",
        "Nature-Based (Wales)",
        "Dementia Peer Support (avg)",
        "Digital Inclusion Volunteering",
    ]
    sroi_low = [4.44, 6.05, 4.02, 3.40, 2.57, 1.17, 1.40]
    sroi_high = [4.44, 6.05, 5.43, 4.69, 4.67, 5.18, 1.80]

    if palette_mode == "accessible":
        base_colour = ACCESSIBLE_SEQUENCE[0]
        range_colour = ACCESSIBLE_SEQUENCE[1]
    else:
        base_colour = "#1E90FF"
        range_colour = "rgba(30, 144, 255, 0.4)"

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=sroi_labels,
            x=sroi_low,
            orientation="h",
            name="Low estimate",
            marker_color=base_colour,
            text=[f"£{v:.2f}" for v in sroi_low],
            textposition="inside",
            textfont=dict(color="white", size=11),
            insidetextanchor="middle",
        )
    )
    fig.add_trace(
        go.Bar(
            y=sroi_labels,
            x=[h - l for l, h in zip(sroi_low, sroi_high)],
            orientation="h",
            name="Range to high",
            marker_color=range_colour,
            text=[f"→ £{h:.2f}" if h != l else "" for l, h in zip(sroi_low, sroi_high)],
            textposition="inside",
            textfont=dict(color="#1E90FF", size=10),
            insidetextanchor="middle",
        )
    )
    fig.update_layout(
        barmode="stack",
        title={
            "text": "<b>SROI Ratios: £ Return per £1 Invested (Wales)</b>",
            "x": 0.5,
            "y": 0.95,
            "xanchor": "center",
            "font": {"size": 16},
        },
        xaxis_title="£ Return per £1",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=200, r=50, t=100, b=80),
        height=450,
        width=900,
        plot_bgcolor=PLOT_BGCOLOUR,
        xaxis=dict(range=[0, 7], gridcolor="white"),
        yaxis=dict(autorange="reversed"),
    )
    fig.add_annotation(
        text="<i>Sources: Sport Wales, WCVA, Mantell Gwynedd, academic studies</i>",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.15,
        showarrow=False,
        font=dict(size=10, color="gray"),
        xanchor="center",
    )
    fig.update_traces(cliponaxis=False)
    _scale_layout(fig, text_scale)
    return fig


def make_volunteering_value_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    categories = [
        "Unpaid Carers (Wales)",
        "Formal Volunteering (E&W, replacement)",
        "Regular Vol. Hours (E&W, 80% median)",
        "Vol. Time Equiv. (Wales, est.)",
        "Wellbeing Benefits (England only)",
    ]
    values = [8.1, 10.3, 5.6, 1.7, 8.26]

    palette = ACCESSIBLE_SEQUENCE if palette_mode == "accessible" else BRAND_SEQUENCE

    fig = go.Figure(
        go.Bar(
            x=categories,
            y=values,
            text=[f"£{v:.1f}bn" for v in values],
            textposition="outside",
            marker_color=palette[: len(categories)],
        )
    )
    fig.update_layout(
        title=dict(
            text="Economic Value of Volunteering & Unpaid Care (£bn)",
            subtitle=dict(
                text="Sources: Knowledge Hub, NCVO, DCMS, Carers UK | Various years",
                font=dict(size=SUBTITLE_FONT),
            ),
        ),
        xaxis_title="",
        yaxis_title="Value (£bn)",
        showlegend=False,
        height=500,
        width=900,
        plot_bgcolor=PLOT_BGCOLOUR,
    )
    fig.update_traces(cliponaxis=False)
    _scale_layout(fig, text_scale)
    return fig


def make_measurement_gap_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    labels_gap = [
        "Registered Charities",
        "WCVA Members",
        "All Active Orgs",
        "Baromedr Wave 1 Respondents",
        "Baromedr Wave 2 Respondents",
    ]
    values_gap = [8000, 3350, 47116, 99, 111]

    palette = ACCESSIBLE_SEQUENCE if palette_mode == "accessible" else BRAND_SEQUENCE

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels_gap,
            y=values_gap,
            text=[f"{v:,}" for v in values_gap],
            textposition="outside",
            marker_color=palette[: len(labels_gap)],
        )
    )
    fig.update_layout(
        title=dict(
            text="The Measurement Gap: Who Gets Counted?",
            subtitle=dict(
                text=(
                    "Sources: Charity Commission, WCVA, WG | Illustrates coverage gaps"
                ),
                font=dict(size=SUBTITLE_FONT),
            ),
        ),
        xaxis_title="",
        yaxis_title="No. of Organisations",
        showlegend=False,
        height=500,
        width=900,
        plot_bgcolor=PLOT_BGCOLOUR,
    )
    fig.update_traces(cliponaxis=False)
    _scale_layout(fig, text_scale)
    return fig


def make_wcva_wg_funding_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    years_wcva = ["2021-22", "2022-23", "2023-24", "2024-25"]
    grant_vals = [16.93, 17.63, 21.71, 24.14]
    contract_vals = [12.78, 0.60, 0.48, 0.33]
    total_vals = [g + c for g, c in zip(grant_vals, contract_vals)]

    if palette_mode == "accessible":
        grants_colour = ACCESSIBLE_SEQUENCE[0]
        contracts_colour = ACCESSIBLE_SEQUENCE[1]
    else:
        grants_colour = "#1E90FF"
        contracts_colour = "#20B2AA"

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=years_wcva,
            y=grant_vals,
            name="Grants",
            marker_color=grants_colour,
            text=[f"£{v:.1f}m" for v in grant_vals],
            textposition="inside",
            textfont=dict(color="white", size=11),
            insidetextanchor="middle",
        )
    )
    fig.add_trace(
        go.Bar(
            x=years_wcva,
            y=contract_vals,
            name="Contracts",
            marker_color=contracts_colour,
            text=[f"£{v:.1f}m" if v > 1 else "" for v in contract_vals],
            textposition="inside",
            textfont=dict(color="white", size=10),
            insidetextanchor="middle",
        )
    )
    fig.update_layout(
        barmode="stack",
        title={
            "text": "<b>Welsh Government Payments to WCVA (£m)</b>",
            "x": 0.5,
            "y": 0.95,
            "xanchor": "center",
            "font": {"size": 16},
        },
        xaxis_title="Financial Year",
        yaxis_title="Amount (£m)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=70, r=50, t=100, b=100),
        height=450,
        width=700,
        plot_bgcolor=PLOT_BGCOLOUR,
        yaxis=dict(gridcolor="white", range=[0, 35]),
    )

    for year, total in zip(years_wcva, total_vals):
        fig.add_annotation(
            x=year,
            y=total + 1,
            text=f"<b>£{total:.1f}m</b>",
            showarrow=False,
            font=dict(size=10, color="#333"),
            yanchor="bottom",
        )

    fig.add_annotation(
        text="<i>Source: Welsh Government FOI ATISN24397 (March 2025)</i>",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.15,
        showarrow=False,
        font=dict(size=10, color="gray"),
        xanchor="center",
    )
    fig.update_traces(cliponaxis=False)
    _scale_layout(fig, text_scale)
    return fig


def make_nlcf_wales_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    nlcf_years = ["2023-24", "2024"]
    nlcf_amounts = [39.2, 36.8]

    colours = (
        ACCESSIBLE_SEQUENCE[:2]
        if palette_mode == "accessible"
        else ["#FF6347", "#FFD700"]
    )

    fig = go.Figure(
        go.Bar(
            x=nlcf_years,
            y=nlcf_amounts,
            text=[f"£{v}m" for v in nlcf_amounts],
            textposition="outside",
            marker_color=colours,
        )
    )
    fig.update_layout(
        title=dict(
            text="National Lottery Community Fund: Wales (£m)",
            subtitle=dict(
                text="Source: NLCF Annual Reports | Over £1bn to Wales in 30 years",
                font=dict(size=SUBTITLE_FONT),
            ),
        ),
        xaxis_title="Year",
        yaxis_title="Amount (£m)",
        showlegend=False,
        height=500,
        width=900,
        plot_bgcolor=PLOT_BGCOLOUR,
    )
    fig.update_traces(cliponaxis=False)
    _scale_layout(fig, text_scale)
    return fig


def make_alignment_heatmap_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    enablers = [
        "Determined leadership",
        "Plans built on data & evidence",
        "Action-focused objectives",
        "Budgets & resources for action",
        "Volunteer-centred approach",
        "Welsh culture, society & language",
        "Engagement with young people",
        "Strong communication",
    ]

    objectives = [
        "Fits modern lifestyles",
        "Valued & impactful",
        "Achieves org objectives",
        "Better volunteer experiences",
        "Stronger support systems",
        "Diverse & accessible",
    ]

    alignment = [
        [1, 2, 2, 1, 2, 1],
        [2, 3, 3, 2, 2, 2],
        [2, 3, 3, 2, 2, 2],
        [3, 3, 3, 2, 3, 2],
        [3, 2, 2, 3, 3, 3],
        [2, 2, 2, 2, 1, 3],
        [3, 2, 2, 3, 2, 3],
        [2, 3, 2, 2, 2, 2],
    ]

    if palette_mode == "accessible":
        colourscale = [
            [0, "#f0f0f0"],
            [0.33, ACCESSIBLE_SEQUENCE[0]],
            [0.67, ACCESSIBLE_SEQUENCE[1]],
            [1.0, ACCESSIBLE_SEQUENCE[2]],
        ]
    else:
        colourscale = [
            [0, "#f0f0f0"],
            [0.33, "#b3d9ff"],
            [0.67, "#3399ff"],
            [1.0, "#0059b3"],
        ]

    fig = go.Figure(
        data=go.Heatmap(
            z=alignment,
            x=objectives,
            y=enablers,
            colorscale=colourscale,
            text=[
                [
                    "Indirect",
                    "Moderate",
                    "Moderate",
                    "Indirect",
                    "Moderate",
                    "Indirect",
                ],
                ["Moderate", "Strong", "Strong", "Moderate", "Moderate", "Moderate"],
                ["Moderate", "Strong", "Strong", "Moderate", "Moderate", "Moderate"],
                ["Strong", "Strong", "Strong", "Moderate", "Strong", "Moderate"],
                ["Strong", "Moderate", "Moderate", "Strong", "Strong", "Strong"],
                ["Moderate", "Moderate", "Moderate", "Moderate", "Indirect", "Strong"],
                ["Strong", "Moderate", "Moderate", "Strong", "Moderate", "Strong"],
                ["Moderate", "Strong", "Moderate", "Moderate", "Moderate", "Moderate"],
            ],
            texttemplate="%{text}",
            textfont={"size": 12},
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        title=dict(
            text="SROI Evidence Alignment with New Approach Framework",
            subtitle=dict(
                text="Strength of link: Enablers (rows) × Objectives (columns)",
                font=dict(size=SUBTITLE_FONT),
            ),
        ),
        xaxis_title="Objectives",
        yaxis_title="Enablers",
        yaxis=dict(autorange="reversed"),
        height=500,
        width=900,
        plot_bgcolor=PLOT_BGCOLOUR,
    )
    _scale_layout(fig, text_scale)
    return fig


def make_framework_flow_plotly_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    fig = go.Figure()

    panel_y0, panel_y1 = 20, 570
    panel_width = 300
    gap = 20

    fig.add_shape(
        type="rect",
        x0=20,
        y0=panel_y0,
        x1=20 + panel_width,
        y1=panel_y1,
        line=dict(color="#aaaa33"),
        fillcolor="#ffffde",
        layer="below",
    )
    mid_x0 = 20 + panel_width + gap
    fig.add_shape(
        type="rect",
        x0=mid_x0,
        y0=panel_y0,
        x1=mid_x0 + panel_width,
        y1=panel_y1,
        line=dict(color="#aaaa33"),
        fillcolor="#ffffde",
        layer="below",
    )
    right_x0 = mid_x0 + panel_width + gap
    fig.add_shape(
        type="rect",
        x0=right_x0,
        y0=panel_y0,
        x1=right_x0 + panel_width,
        y1=panel_y1,
        line=dict(color="#aaaa33"),
        fillcolor="#ffffde",
        layer="below",
    )

    fig.add_annotation(
        x=(20 + 20 + panel_width) / 2,
        y=panel_y1 + 15,
        text="Enablers",
        showarrow=False,
        font=dict(size=12),
    )
    fig.add_annotation(
        x=(mid_x0 + mid_x0 + panel_width) / 2,
        y=panel_y1 + 15,
        text="Objectives",
        showarrow=False,
        font=dict(size=12),
    )
    fig.add_annotation(
        x=(right_x0 + right_x0 + panel_width) / 2,
        y=panel_y1 + 15,
        text="Vision Made Real",
        showarrow=False,
        font=dict(size=12),
    )

    en_x = 20 + panel_width / 2
    obj_x = mid_x0 + panel_width / 2
    vis_x = right_x0 + panel_width / 2

    en_y = [110, 210, 310, 510]
    obj_y = [110, 210, 310, 410]
    vis_y = [180, 310, 440]

    en_labels = [
        "Leadership",
        "Data & Evidence",
        "Resources & Budgets",
        "Volunteer-Centred",
    ]
    obj_labels = [
        "Valued & Impactful £4.44 - SROI Sport Wales",
        "Fits Modern Life - 32% volunteering rate",
        "Stronger Support £1.39m - NW CVCs",
        "Diverse & Accessible - Cyfle £6.05 SROI",
    ]
    vis_labels = [
        "Way of Life - £1.7bn vol. value",
        "Wellbeing Improved - £8.1bn carers",
        "Safe & Sustainable - 47,116 orgs",
    ]

    node_width = 220
    node_height = 60

    def add_nodes(xs, ys, labels):
        for x, y, label in zip(xs, ys, labels):
            fig.add_shape(
                type="rect",
                x0=x - node_width / 2,
                y0=y - node_height / 2,
                x1=x + node_width / 2,
                y1=y + node_height / 2,
                line=dict(color="#9370DB"),
                fillcolor="#ECECFF",
            )
            fig.add_annotation(
                x=x,
                y=y,
                text=label,
                showarrow=False,
                font=dict(size=11),
            )

    add_nodes([en_x] * len(en_y), en_y, en_labels)
    add_nodes([obj_x] * len(obj_y), obj_y, obj_labels)
    add_nodes([vis_x] * len(vis_y), vis_y, vis_labels)

    def add_arrow(x0, y0, x1, y1):
        fig.add_annotation(
            x=x1,
            y=y1,
            ax=x0,
            ay=y0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1,
            arrowwidth=1.5,
            arrowcolor="#333333",
        )

    add_arrow(en_x + node_width / 2, en_y[0], obj_x - node_width / 2, obj_y[0])
    add_arrow(en_x + node_width / 2, en_y[1], obj_x - node_width / 2, obj_y[0])
    add_arrow(en_x + node_width / 2, en_y[1], obj_x - node_width / 2, obj_y[3])
    add_arrow(en_x + node_width / 2, en_y[2], obj_x - node_width / 2, obj_y[2])
    add_arrow(en_x + node_width / 2, en_y[3], obj_x - node_width / 2, obj_y[1])
    add_arrow(en_x + node_width / 2, en_y[3], obj_x - node_width / 2, obj_y[3])

    add_arrow(obj_x + node_width / 2, obj_y[0], vis_x - node_width / 2, vis_y[0])
    add_arrow(obj_x + node_width / 2, obj_y[1], vis_x - node_width / 2, vis_y[0])
    add_arrow(obj_x + node_width / 2, obj_y[2], vis_x - node_width / 2, vis_y[2])
    add_arrow(obj_x + node_width / 2, obj_y[3], vis_x - node_width / 2, vis_y[1])

    fig.update_layout(
        xaxis=dict(
            visible=False,
            range=[0, right_x0 + panel_width + 20],
        ),
        yaxis=dict(
            visible=False,
            range=[0, 600],
        ),
        plot_bgcolor="white",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        width=1000,
        height=600,
        title_text="New Approach Framework Flow (Enablers → Objectives → Vision)",
        title_x=0.5,
    )
    _scale_layout(fig, text_scale)
    return fig


def make_timeline_figure(
    *, palette_mode: str = "brand", text_scale: float = 1.0
) -> go.Figure:
    phases = [
        "Baseline data collection",
        "50 orgs adopt vision",
        "Dashboard built (D&I)",
        "Communities of Practice",
        "Intermediate objectives",
        "Measurable vision progress",
        "Independent evaluation",
    ]
    start_months = [0, 0, 6, 3, 12, 36, 48]
    durations = [12, 18, 12, 24, 24, 24, 12]
    if palette_mode == "accessible":
        colors = ACCESSIBLE_SEQUENCE[: len(phases)]
    else:
        colors = [
            "#1E90FF",
            "#20B2AA",
            "#FF6347",
            "#9370DB",
            "#32CD32",
            "#FFD700",
            "#FF69B4",
        ]

    fig = go.Figure()
    for i, (phase, start, dur) in enumerate(zip(phases, start_months, durations)):
        fig.add_trace(
            go.Bar(
                y=[phase],
                x=[dur],
                base=[start],
                orientation="h",
                name=phase,
                marker_color=colors[i],
                text=[f"{dur} months"],
                textposition="inside",
                showlegend=False,
            )
        )

    for yr, label in [
        (0, "Jul 2025"),
        (12, "Jul 2026"),
        (24, "Jul 2027"),
        (36, "Jul 2028"),
        (48, "Jul 2029"),
        (60, "Jul 2030"),
    ]:
        fig.add_vline(x=yr, line_dash="dot", line_color="gray", opacity=0.5)

    fig.update_layout(
        title=dict(
            text="New Approach Implementation Timeline",
            subtitle=dict(
                text=(
                    "Source: WG/WCVA New Approach (2025) | Key milestones from launch"
                ),
                font=dict(size=SUBTITLE_FONT),
            ),
        ),
        xaxis_title="Months from Launch (Jul 2025)",
        yaxis_title="",
        barmode="overlay",
        xaxis=dict(range=[-1, 65], dtick=12),
        height=500,
        width=900,
        plot_bgcolor=PLOT_BGCOLOUR,
    )
    fig.update_traces(cliponaxis=False)
    _scale_layout(fig, text_scale)
    return fig


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
