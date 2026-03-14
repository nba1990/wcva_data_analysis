from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from src.sroi_charts import sroi_figures


def _trace_colors(fig: go.Figure) -> list:
    """Extract marker/line/colorscale colors from traces via figure dict."""
    out: Any = []
    for trace_dict in fig.to_dict().get("data", []):
        marker = (trace_dict.get("marker") or {}) or {}
        line = (trace_dict.get("line") or {}) or {}
        c = marker.get("color") or line.get("color")
        if c is not None:
            out.extend(c if isinstance(c, (list, tuple)) else [c])
        # Heatmaps use colorscale: [[0, color0], [0.5, color1], ...]
        for pair in trace_dict.get("colorscale") or []:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                out.append(pair[1])
    return out


def _assert_palette_changes(factory, **kwargs) -> None:
    fig_brand = factory(palette_mode="brand", text_scale=1.0, **kwargs)
    fig_accessible = factory(palette_mode="accessible", text_scale=1.0, **kwargs)
    assert isinstance(fig_brand, go.Figure)
    assert isinstance(fig_accessible, go.Figure)

    colours_brand = _trace_colors(fig_brand)
    colours_accessible = _trace_colors(fig_accessible)
    if colours_brand or colours_accessible:
        assert colours_brand != colours_accessible, "palette_mode should change colours"


def _assert_text_scale_changes(factory, **kwargs) -> None:
    fig_default = factory(palette_mode="brand", text_scale=1.0, **kwargs)
    fig_scaled = factory(palette_mode="brand", text_scale=1.3, **kwargs)

    layout_default = fig_default.to_dict()["layout"]
    layout_scaled = fig_scaled.to_dict()["layout"]

    base_font = layout_default.get("font", {}).get("size")
    base_title_font = layout_default.get("title", {}).get("font", {}).get("size")
    scaled_font = layout_scaled.get("font", {}).get("size")
    scaled_title_font = layout_scaled.get("title", {}).get("font", {}).get("size")

    # Guard against missing values in very old Plotly versions
    if base_font is not None and scaled_font is not None:
        assert scaled_font > base_font
    if base_title_font is not None and scaled_title_font is not None:
        assert scaled_title_font > base_title_font


def test_all_sroi_factories_return_figures_and_have_titles() -> None:
    factories = [
        sroi_figures.make_funding_flows_figure,
        sroi_figures.make_sroi_comparison_figure,
        sroi_figures.make_volunteering_value_figure,
        sroi_figures.make_measurement_gap_figure,
        sroi_figures.make_wcva_wg_funding_figure,
        sroi_figures.make_nlcf_wales_figure,
        sroi_figures.make_alignment_heatmap_figure,
        sroi_figures.make_framework_flow_plotly_figure,
        sroi_figures.make_timeline_figure,
    ]

    for factory in factories:
        fig = factory()
        assert isinstance(fig, go.Figure)
        layout = fig.to_dict()["layout"]
        # Some charts use dict title, some use plain string; just assert non‑empty
        title = layout.get("title")
        if isinstance(title, dict):
            text = title.get("text", "")
        else:
            text = title or ""
        assert str(text).strip(), f"{factory.__name__} should set a title"


def test_palette_mode_and_text_scale_behaviour() -> None:
    factories = [
        sroi_figures.make_funding_flows_figure,
        sroi_figures.make_sroi_comparison_figure,
        sroi_figures.make_volunteering_value_figure,
        sroi_figures.make_measurement_gap_figure,
        sroi_figures.make_wcva_wg_funding_figure,
        sroi_figures.make_nlcf_wales_figure,
        sroi_figures.make_alignment_heatmap_figure,
        sroi_figures.make_framework_flow_plotly_figure,
        sroi_figures.make_timeline_figure,
    ]

    for factory in factories:
        _assert_palette_changes(factory)
        _assert_text_scale_changes(factory)
