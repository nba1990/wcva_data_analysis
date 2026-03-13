import base64
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, Optional

import plotly.graph_objects as go

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
    width: Optional[int] = None,
    height: Optional[int] = None,
    png: bool = True,
    svg: bool = True,
    meta: Optional[Dict[str, str]] = None,
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


def _parse_transform_translate(transform: str) -> Optional[Iterable[float]]:
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
        search_group = node_group
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
    import subprocess
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
                subprocess.run(
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
                subprocess.run(
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
            with urllib.request.urlopen(req) as resp, open(png_path, "wb") as out:
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
            with urllib.request.urlopen(req) as resp, open(svg_path, "wb") as out:
                out.write(resp.read())

    if svg:
        normalize_mermaid_svg_text(svg_path)


# ============ CHART 1: Funding Flows into Welsh Voluntary Sector (Sankey-style bar) ============


def create_funding_flows_chart() -> None:
    print(f"Creating Chart 1: Funding flows...")

    funding_sources = [
        "WG Direct Grants",
        "WG via WCVA",
        "NLCF Wales",
        "UK SPF Wales",
        "Comm. Facilities Prog. (~£7m)",
        "Other (Trusts, Corporate, etc.)",
    ]
    amounts = [668, 24.5, 39, 195, 7, 50]

    fig = go.Figure(
        go.Bar(
            x=amounts,
            y=funding_sources,
            orientation="h",
            text=[f"£{v:.0f}m" if v >= 1 else f"£{v:.1f}m" for v in amounts],
            textposition="outside",
            marker_color=[
                "#1E90FF",
                "#20B2AA",
                "#FF6347",
                "#9370DB",
                "#32CD32",
                "#FFD700",
            ],
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
    print(f"Creating Chart 2: SROI Comparison...")

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

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=sroi_labels,
            x=sroi_low,
            orientation="h",
            name="Low estimate",
            marker_color="#1E90FF",
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
            marker_color="rgba(30, 144, 255, 0.4)",
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
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
        ),
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
        y=-0.12,
        showarrow=False,
        font=dict(size=10, color="gray"),
        xanchor="center",
    )
    fig.update_traces(cliponaxis=False)

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
    print(f"Creating Chart 3: Volunteering Value...")

    categories = [
        "Unpaid Carers (Wales)",
        "Formal Volunteering (E&W, replacement)",
        "Regular Vol. Hours (E&W, 80% median)",
        "Vol. Time Equiv. (Wales, est.)",
        "Wellbeing Benefits (England only)",
    ]
    values = [8.1, 10.3, 5.6, 1.7, 8.26]

    fig = go.Figure(
        go.Bar(
            x=categories,
            y=values,
            text=[f"£{v:.1f}bn" for v in values],
            textposition="outside",
            marker_color=[
                "#FF6347",
                "#1E90FF",
                "#20B2AA",
                "#9370DB",
                "#FFD700",
            ],
        )
    )
    fig.update_layout(
        title=dict(
            text="Economic Value of Volunteering & Unpaid Care (£bn)",
            subtitle=dict(
                text=(
                    "Sources: Knowledge Hub, NCVO, DCMS, Carers UK | Various years"
                ),
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

    print(f"Creating Chart 4: The Measurement Gap...")

    labels_gap = [
        "Registered Charities",
        "WCVA Members",
        "All Active Orgs",
        "Baromedr Wave 1 Respondents",
        "Baromedr Wave 2 Respondents",
    ]
    values_gap = [
        8000,
        3350,
        47116,
        99,
        111,
    ]  # approximate number of respondents for Baromedr Waves 1 and 2

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels_gap,
            y=values_gap,
            text=[f"{v:,}" for v in values_gap],
            textposition="outside",
            marker_color=[
                "#1E90FF",
                "#20B2AA",
                "#FF6347",
                "#9370DB",
                "#FFD700",
            ],
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
    print(f"Creating Chart 5: WCVA Funding Flows from WG Over Time...")

    years_wcva = ["2021-22", "2022-23", "2023-24", "2024-25"]
    grant_vals = [16.93, 17.63, 21.71, 24.14]
    contract_vals = [12.78, 0.60, 0.48, 0.33]
    total_vals = [g + c for g, c in zip(grant_vals, contract_vals)]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=years_wcva,
            y=grant_vals,
            name="Grants",
            marker_color="#1E90FF",
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
            marker_color="#20B2AA",
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
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
        ),
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
        y=-0.22,
        showarrow=False,
        font=dict(size=10, color="gray"),
        xanchor="center",
    )
    fig.update_traces(cliponaxis=False)

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
    print(f"Creating Chart 6: NLCF Wales Funding...")

    nlcf_years = ["2023-24", "2024"]
    nlcf_amounts = [39.2, 36.8]

    fig = go.Figure(
        go.Bar(
            x=nlcf_years,
            y=nlcf_amounts,
            text=[f"£{v}m" for v in nlcf_amounts],
            textposition="outside",
            marker_color=["#FF6347", "#FFD700"],
        )
    )
    fig.update_layout(
        title=dict(
            text="National Lottery Community Fund: Wales (£m)",
            subtitle=dict(
                text=(
                    "Source: NLCF Annual Reports | Over £1bn to Wales in 30 years"
                ),
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
    print(f"Creating Chart 7: Mapping Table HeatMap...")

    # This is a visual heatmap-style table showing alignment strength
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

    # Alignment scores (0-3): 0=no link, 1=indirect, 2=moderate, 3=strong direct SROI evidence
    # Rows = enablers, Cols = objectives
    alignment = [
        [1, 2, 2, 1, 2, 1],  # leadership
        [2, 3, 3, 2, 2, 2],  # data/evidence — strong link to SROI
        [2, 3, 3, 2, 2, 2],  # action objectives
        [3, 3, 3, 2, 3, 2],  # budgets — directly tied to SROI ratios
        [3, 2, 2, 3, 3, 3],  # volunteer-centred
        [2, 2, 2, 2, 1, 3],  # Welsh culture
        [3, 2, 2, 3, 2, 3],  # young people
        [2, 3, 2, 2, 2, 2],  # communication
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=alignment,
            x=objectives,
            y=enablers,
            colorscale=[
                [0, "#f0f0f0"],
                [0.33, "#b3d9ff"],
                [0.67, "#3399ff"],
                [1.0, "#0059b3"],
            ],
            text=[
                ["Indirect", "Moderate", "Moderate", "Indirect", "Moderate", "Indirect"],
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
    print(f"Creating Chart 8: Mermaid Flowchart...")

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

    fig = go.Figure()

    # Column background panels
    panel_y0, panel_y1 = 20, 570
    panel_width = 300
    gap = 20

    # Enablers panel
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
    # Middle objectives panel
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
    # Vision panel
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

    # Panel titles
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

    # Node positions
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

    # Arrows (matching the Mermaid logic)
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

    # E1 -> O1
    add_arrow(en_x + node_width / 2, en_y[0], obj_x - node_width / 2, obj_y[0])
    # E2 -> O1, O4
    add_arrow(en_x + node_width / 2, en_y[1], obj_x - node_width / 2, obj_y[0])
    add_arrow(en_x + node_width / 2, en_y[1], obj_x - node_width / 2, obj_y[3])
    # E3 -> O3
    add_arrow(en_x + node_width / 2, en_y[2], obj_x - node_width / 2, obj_y[2])
    # E4 -> O2, O4
    add_arrow(en_x + node_width / 2, en_y[3], obj_x - node_width / 2, obj_y[1])
    add_arrow(en_x + node_width / 2, en_y[3], obj_x - node_width / 2, obj_y[3])

    # O1/O2/O3/O4 -> V1/V2/V3
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
    print(f"Creating Chart 9: Implementation Timeline...")

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

