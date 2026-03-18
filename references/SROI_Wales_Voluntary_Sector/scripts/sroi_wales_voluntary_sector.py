# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

import base64
import json
import os
import re
import urllib.request
from collections.abc import Iterable

import plotly.graph_objects as go
from defusedxml import ElementTree as ET

from src.sroi_charts.sroi_figures import (
    make_alignment_heatmap_figure,
    make_framework_flow_plotly_figure,
    make_funding_flows_figure,
    make_measurement_gap_figure,
    make_nlcf_wales_figure,
    make_sroi_comparison_figure,
    make_timeline_figure,
    make_volunteering_value_figure,
    make_wcva_wg_funding_figure,
)

OUTPUT_DIR = "../output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SUBTITLE_FONT = 10
PLOT_BGCOLOUR = "rgb(229, 236, 246)"


def write_meta(basename: str, caption: str, description: str) -> None:
    """Write a simple JSON sidecar meta file for a chart."""
    meta_path = os.path.join(OUTPUT_DIR, f"{basename}.png.meta.json")
    with open(meta_path, "w") as f:
        json.dump({"caption": caption, "description": description}, f)


def save_plotly_figure(
    fig: go.Figure,
    basename: str,
    *,
    width: int | None = None,
    height: int | None = None,
    png: bool = True,
    svg: bool = True,
    meta: dict[str, str] | None = None,
) -> None:
    """Save a Plotly figure in a consistent way (PNG/SVG + optional meta)."""
    if width is not None or height is not None:
        fig.update_layout(width=width, height=height)

    png_path = os.path.join(OUTPUT_DIR, f"{basename}.png")
    svg_path = os.path.join(OUTPUT_DIR, f"{basename}.svg")

    if png:
        fig.write_image(png_path, scale=2)
    if svg:
        fig.write_image(svg_path, format="svg")

    if meta:
        write_meta(basename, caption=meta["caption"], description=meta["description"])


def _parse_transform_translate(transform: str) -> Iterable[float] | None:
    """Extract x, y from a simple 'translate(x,y)' transform string."""
    if not transform:
        return None
    match = re.search(r"translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", transform)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def normalize_mermaid_svg_text(svg_path: str) -> None:
    """Replace Mermaid foreignObject labels with plain <text> elements.

    This improves compatibility with tools that don't support HTML inside SVG.
    """
    if not os.path.exists(svg_path):
        return

    # Preserve namespaces
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    tree = ET.parse(svg_path)
    root = tree.getroot()
    svg_ns = "http://www.w3.org/2000/svg"

    parent_map = {child: parent for parent in tree.iter() for child in parent}

    foreign_tag = f"{{{svg_ns}}}foreignObject"
    rect_tag = f"{{{svg_ns}}}rect"
    text_tag = f"{{{svg_ns}}}text"

    for fo in list(root.iter(foreign_tag)):
        # Try to get label text from any descendant <p> (HTML namespace is ignored)
        label_text = None
        for el in fo.iter():
            if el.tag.endswith("p") and (el.text or "").strip():
                label_text = el.text.strip()
                break

        # If there is no label text, just strip the foreignObject to be safe.
        if not label_text:
            parent = parent_map.get(fo)
            if parent is not None:
                parent.remove(fo)
            continue

        # Determine what kind of group this belongs to (node vs cluster label)
        node_group = None
        cluster_group = None
        current = parent_map.get(fo)
        while current is not None:
            cls = current.attrib.get("class", "")
            classes = cls.split()
            if "node" in classes:
                node_group = current
                break
            if "cluster-label" in classes and node_group is None:
                node_group = current
            if "cluster" in classes and cluster_group is None:
                cluster_group = current
            current = parent_map.get(current)

        if node_group is None and cluster_group is None:
            # Nothing we can sensibly attach to
            parent = parent_map.get(fo)
            if parent is not None:
                parent.remove(fo)
            continue

        # Find an appropriate rect: for normal nodes, it is in the node group;
        # for cluster labels, the rect is on the enclosing cluster group.
        rect = None
        if node_group is not None:
            for candidate in node_group.findall(rect_tag):
                cls = candidate.attrib.get("class", "")
                if "label-container" in cls:
                    rect = candidate
                    break
            if rect is None:
                rects = node_group.findall(rect_tag)
                if rects:
                    rect = rects[0]

        if rect is None and cluster_group is not None:
            rects = cluster_group.findall(rect_tag)
            if rects:
                rect = rects[0]

        if rect is None:
            # As a last resort, don't crash; just drop the foreignObject.
            parent = parent_map.get(fo)
            if parent is not None:
                parent.remove(fo)
            continue

        x = float(rect.attrib.get("x", "0"))
        y = float(rect.attrib.get("y", "0"))
        w = float(rect.attrib.get("width", "0"))
        h = float(rect.attrib.get("height", "0"))
        cx = x + w / 2.0
        cy = y + h / 2.0

        # Account for group translate, if present. For cluster labels, the label
        # group itself already holds the intended anchor position, so we prefer
        # its transform over the rectangle centre.
        transform_group = None
        if node_group is not None:
            transform_group = node_group
        elif cluster_group is not None:
            transform_group = cluster_group

        classes_node = []
        if node_group is not None:
            classes_node = node_group.attrib.get("class", "").split()

        if "cluster-label" in classes_node:
            # Use the cluster-label group's transform directly as the anchor.
            transform = node_group.attrib.get("transform", "")
            translate = _parse_transform_translate(transform)
            if translate:
                cx, cy = translate
                cy += 12  # small offset to sit just below the top edge
        else:
            transform = ""
            if transform_group is not None:
                transform = transform_group.attrib.get("transform", "")
            translate = _parse_transform_translate(transform)
            if translate:
                tx, ty = translate
                cx += tx
                cy += ty

        text_el = ET.Element(text_tag)
        text_el.text = label_text
        text_el.set("x", f"{cx}")
        text_el.set("y", f"{cy}")
        text_el.set("text-anchor", "middle")
        text_el.set("alignment-baseline", "middle")
        text_el.set("fill", "#333333")

        # Insert text as a sibling inside the most specific group we have
        if node_group is not None:
            target_group = node_group
        elif cluster_group is not None:
            target_group = cluster_group
        else:
            target_group = parent_map.get(fo)
        if target_group is not None:
            target_group.append(text_el)

        # Remove the original foreignObject to avoid overlapping content
        parent = parent_map.get(fo)
        if parent is not None:
            parent.remove(fo)

    tree.write(svg_path, encoding="utf-8", xml_declaration=True)


def create_mermaid_diagram(
    mermaid_code: str,
    basename: str,
    *,
    png: bool = True,
    svg: bool = True,
    width: int = 800,
    height: int = 600,
) -> None:
    """Render a Mermaid diagram to PNG/SVG using mmdc or mermaid.ink, then normalise SVG text."""
    import shutil
    import subprocess  # nosec B404
    import tempfile

    png_path = os.path.join(OUTPUT_DIR, f"{basename}.png")
    svg_path = os.path.join(OUTPUT_DIR, f"{basename}.svg")

    mmdc = shutil.which("mmdc")
    if mmdc:
        chrome = (
            shutil.which("google-chrome-stable")
            or shutil.which("google-chrome")
            or shutil.which("chromium-browser")
            or shutil.which("chromium")
        )
        env = os.environ.copy()
        if chrome:
            env["PUPPETEER_EXECUTABLE_PATH"] = chrome

        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(mermaid_code)
            input_path = f.name
        try:
            if png:
                subprocess.run(  # nosec B603
                    [
                        mmdc,
                        "-i",
                        input_path,
                        "-o",
                        png_path,
                        "-w",
                        str(width),
                        "-H",
                        str(height),
                    ],
                    check=True,
                    env=env,
                )
            if svg:
                subprocess.run(  # nosec B603
                    [
                        mmdc,
                        "-i",
                        input_path,
                        "-o",
                        svg_path,
                        "-w",
                        str(width),
                        "-H",
                        str(height),
                    ],
                    check=True,
                    env=env,
                )
        finally:
            os.remove(input_path)
    else:
        encoded = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("ascii")
        if png:
            url_png = f"https://mermaid.ink/img/{encoded}?width={width}&height={height}"
            req = urllib.request.Request(
                url_png,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                    ),
                },
            )
            with (
                urllib.request.urlopen(req) as resp,  # nosec B310
                open(png_path, "wb") as out,
            ):
                out.write(resp.read())

        if svg:
            url_svg = f"https://mermaid.ink/svg/{encoded}"
            req = urllib.request.Request(
                url_svg,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                    ),
                },
            )
            with (
                urllib.request.urlopen(req) as resp,  # nosec B310
                open(svg_path, "wb") as out,
            ):
                out.write(resp.read())

    if svg:
        normalize_mermaid_svg_text(svg_path)


# ============ CHART 1: Funding Flows into Welsh Voluntary Sector (Sankey-style bar) ============


def create_funding_flows_chart() -> None:
    print("Creating Chart 1: Funding flows...")

    fig = make_funding_flows_figure()

    save_plotly_figure(
        fig,
        "funding_flows",
        meta={
            "caption": "Estimated annual public funding flows into the Welsh voluntary sector",
            "description": "Horizontal bar chart showing major funding sources",
        },
    )

    print("Chart 1 - Created!")


# ============ CHART 2: SROI Ratios Comparison ============


def create_sroi_comparison_chart() -> None:
    print("Creating Chart 2: SROI Comparison...")

    fig = make_sroi_comparison_figure()

    save_plotly_figure(
        fig,
        "sroi_comparison",
        meta={
            "caption": (
                "SROI ratios from Wales-based studies showing £ return per £1 invested"
            ),
            "description": (
                "Stacked horizontal bar chart comparing SROI ratios across "
                "different Welsh voluntary sector programmes"
            ),
        },
    )

    print("Chart 2 - Created!")


# ============ CHART 3: Volunteering Economic Value Pyramid ============


def create_volunteering_value_chart() -> None:
    print("Creating Chart 3: Volunteering Value...")

    fig = make_volunteering_value_figure()

    save_plotly_figure(
        fig,
        "volunteering_value",
        meta={
            "caption": (
                "Economic value of volunteering and unpaid care in billions of pounds"
            ),
            "description": (
                "Bar chart showing different valuations of volunteering and unpaid care"
            ),
        },
    )

    print("Chart 3 - Created!")


# ============ CHART 4: The Measurement Gap ============


def create_measurement_gap_chart() -> None:
    # Refer: https://committees.parliament.uk/writtenevidence/70504/html/
    # Refer: https://www.gov.wales/third-sector-scheme-annual-report-2023-2025-html
    # Refer: https://baromedr.cymru/en/respondents-profile/
    # Refer: https://covid19.public-inquiry.uk/wp-content/uploads/2023/07/21173118/INQ000177813-1.pdf

    print("Creating Chart 4: The Measurement Gap...")

    fig = make_measurement_gap_figure()

    save_plotly_figure(
        fig,
        "measurement_gap",
        meta={
            "caption": (
                "The measurement gap: number of organisations by "
                "registration/coverage type"
            ),
            "description": (
                "Bar chart showing difference between registered charities, WCVA "
                "members, total active orgs, and Baromedr respondents"
            ),
        },
    )

    print("Chart 4 - Created!")


# ============ CHART 5: WCVA Funding from WG Over Time ============


def create_wcva_funding_chart() -> None:
    print("Creating Chart 5: WCVA Funding Flows from WG Over Time...")

    fig = make_wcva_wg_funding_figure()

    save_plotly_figure(
        fig,
        "wcva_wg_funding",
        meta={
            "caption": (
                "Welsh Government payments to WCVA by grants and contracts 2021-2025"
            ),
            "description": (
                "Stacked bar chart showing grant and contract payments from Welsh "
                "Government to WCVA over four financial years"
            ),
        },
    )

    print("Chart 5 - Created!")


# ============ CHART 6: NLCF Wales Over Time ============


def create_nlcf_wales_chart() -> None:
    print("Creating Chart 6: NLCF Wales Funding...")

    fig = make_nlcf_wales_figure()

    save_plotly_figure(
        fig,
        "nlcf_wales",
        meta={
            "caption": "National Lottery Community Fund grants to Wales",
            "description": "Bar chart showing NLCF grants to Wales in recent years",
        },
    )

    print("Chart 6 - Created!")


# ============ CHART 7: Mapping Table — Enablers → SROI Evidence ============


def create_alignment_heatmap() -> None:
    print("Creating Chart 7: Mapping Table HeatMap...")

    fig = make_alignment_heatmap_figure()

    save_plotly_figure(
        fig,
        "alignment_heatmap",
        meta={
            "caption": (
                "Heatmap showing alignment strength between New Approach enablers "
                "and objectives, supported by SROI evidence"
            ),
            "description": (
                "Heatmap matrix mapping New Approach to Volunteering framework "
                "enablers against objectives with SROI evidence strength ratings"
            ),
        },
    )

    print("Chart 7 - Created!")


# ============ CHART 8: Mermaid Flowchart — Enablers → Objectives → Vision ============


def create_framework_flow_diagram() -> None:
    print("Creating Chart 8: Mermaid Flowchart...")

    mermaid_code = """flowchart LR
    subgraph E["Enablers"]
        E1["Leadership"]
        E2["Data & Evidence"]
        E3["Resources & Budgets"]
        E4["Volunteer-Centred"]
    end

    subgraph O["Objectives"]
        O1["Valued & Impactful £4.44 - SROI Sport Wales"]
        O2["Fits Modern Life - 32% volunteering rate"]
        O3["Stronger Support £1.39m - NW CVCs"]
        O4["Diverse & Accessible - Cyfle £6.05 SROI"]
    end

    subgraph V["Vision Made Real"]
        V1["Way of Life - £1.7bn vol. value"]
        V2["Wellbeing Improved - £8.1bn carers"]
        V3["Safe & Sustainable - 47,116 orgs"]
    end

    E1 --> O1
    E2 --> O1
    E2 --> O4
    E3 --> O3
    E4 --> O2
    E4 --> O4
    O1 --> V1
    O2 --> V1
    O3 --> V3
    O4 --> V2
"""

    create_mermaid_diagram(
        mermaid_code,
        "framework_flow_mermaid",
        png=True,
        svg=False,
        width=1400,
        height=700,
    )

    write_meta(
        "framework_flow_mermaid",
        caption=(
            "New Approach framework flow: Enablers → Objectives → Vision, "
            "with SROI data points"
        ),
        description=(
            "Mermaid flowchart showing how the New Approach to Volunteering framework "
            "connects enablers through objectives to the vision, annotated with key "
            "SROI figures from the evidence base"
        ),
    )

    print("Chart 8 - Created!")


def create_framework_flow_chart_plotly() -> None:
    """Plotly-based version of the framework flow for clean SVG export."""
    print("Creating Chart 8b: Framework Flow (Plotly)...")

    fig = make_framework_flow_plotly_figure()

    save_plotly_figure(
        fig,
        "framework_flow",
        meta={
            "caption": (
                "New Approach framework flow: Enablers → Objectives → Vision, "
                "with SROI data points (Plotly version)"
            ),
            "description": (
                "Plotly flowchart showing how the New Approach to Volunteering "
                "framework connects enablers through objectives to the vision, "
                "annotated with key SROI figures from the evidence base"
            ),
        },
    )

    print("Chart 8b - Created!")


# ============ CHART 9: Implementation Timeline ============


def create_implementation_timeline_chart() -> None:
    print("Creating Chart 9: Implementation Timeline...")

    fig = make_timeline_figure()

    save_plotly_figure(
        fig,
        "timeline",
        meta={
            "caption": (
                "Implementation timeline for the New Approach to Volunteering in Wales"
            ),
            "description": (
                "Gantt-style horizontal bar chart showing implementation phases and "
                "their durations from July 2025 launch"
            ),
        },
    )

    print("Chart 9 - Created!")


def create_charts() -> None:
    print("======== PROCESS START ========")
    create_funding_flows_chart()
    create_sroi_comparison_chart()
    create_volunteering_value_chart()
    create_measurement_gap_chart()
    create_wcva_funding_chart()
    create_nlcf_wales_chart()
    create_alignment_heatmap()
    create_framework_flow_diagram()
    create_framework_flow_chart_plotly()
    create_implementation_timeline_chart()
    print("======== PROCESS END ========")
    print(f"All charts created successfully at: {OUTPUT_DIR}")


if __name__ == "__main__":
    create_charts()
# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
