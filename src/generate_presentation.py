"""
Generate dual-format executive presentation from Baromedr Cymru Wave 2 data.

Output 1: Self-contained reveal.js HTML slide deck  (output/presentation.html)
Output 2: Structured PDF with TOC and bookmarks      (output/presentation.pdf)

Run: python -m src.generate_presentation
"""

from __future__ import annotations

import base64
import io
from datetime import date
import pandas as pd
from pathlib import Path

from fpdf import FPDF
from html import escape
from typing import Mapping, Sequence

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import load_dataset
from src.config import (
    DEMAND_ORDER, EXPECT_DEMAND_ORDER, EXPECT_FINANCIAL_ORDER,
    FINANCIAL_ORDER, OUTPUT_DIR, WCVA_BRAND, AltTextConfig, resolve_grouping,
)
from src.wave_context import WAVE1_CONTEXT
from src.eda import (
    profile_summary, demand_and_outlook, volunteer_recruitment_analysis,
    volunteer_retention_analysis, workforce_operations, volunteering_types,
    executive_highlights, finance_recruitment_cross,
)
from src.charts import (
    horizontal_bar_ranked, stacked_bar_ordinal, donut_chart,
)
from src.narratives import demand_finance_scissor_phrase, recruitment_vs_retention_phrase


CHART_W, CHART_H = 1200, 550


def _fig_to_base64(fig, width: int = CHART_W, height: int = CHART_H) -> str:
    """Export a Plotly figure to a base64-encoded PNG string."""
    img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
    return base64.b64encode(img_bytes).decode()


def _fig_to_bytes(fig, width: int = CHART_W, height: int = CHART_H) -> bytes:
    return fig.to_image(format="png", width=width, height=height, scale=2)


def render_executive_insights_list_html(
    items: Sequence[Mapping[str, object]],
    *,
    title_key: str = "title",
    detail_key: str = "detail",
    rank_key: str | None = "rank",
    type_key: str | None = None,
    ordered: bool = True,
) -> str:
    """Render a list of insights as HTML."""
    list_tag = "ol" if ordered else "ul"
    parts: list[str] = [f"<{list_tag}>"]

    sorted_items = (
        sorted(items, key=lambda x: x.get(rank_key, 0))
        if rank_key
        else list(items)
    )

    for item in sorted_items:
        title = escape(str(item[title_key]))
        detail = escape(str(item[detail_key]))

        line = f"<strong>{title}</strong><br>{detail}"

        if type_key and item.get(type_key):
            item_type = escape(str(item[type_key]).capitalize())
            line += f"<br><em>{item_type}</em>"

        parts.append(f"<li>{line}</li>")

    parts.append(f"</{list_tag}>")
    return "".join(parts)

# ---------------------------------------------------------------------------
# Slide content builder
# ---------------------------------------------------------------------------

def build_slides(df, palette_mode: str) -> list[dict]:
    """Build the 10-slide structure with chart images and narrative text."""
    n = len(df)
    prof = profile_summary(df)
    dem = demand_and_outlook(df)
    rec = volunteer_recruitment_analysis(df)
    ret = volunteer_retention_analysis(df)
    wf = workforce_operations(df)
    vt = volunteering_types(df)
    highlights = executive_highlights(df)
    cross = finance_recruitment_cross(df)

    highlights_html = render_executive_insights_list_html(
        highlights,
        title_key="title",
        detail_key="detail",
        rank_key="rank",
        type_key="type",
        ordered=True,
    )

    alt_config = AltTextConfig(value_col="value", count_col="count", pct_col="pct", sample_size=n)
    
    # --- Pre-generate chart images ---
    fig_size = donut_chart(
        list(prof["org_size"].keys()), list(prof["org_size"].values()),
        "Respondent profile by organisation size", n,
    )
    grouper, group_order = resolve_grouping(DEMAND_ORDER)
    TITLE = "Demand change (last 3 months)"
    fig_demand = stacked_bar_ordinal(dem["demand"], TITLE, n, height=180, mode=palette_mode, alt_config=alt_config,
                                     grouper=grouper, group_order=group_order)

    grouper, group_order = resolve_grouping(FINANCIAL_ORDER)
    TITLE = "Financial position change"
    fig_financial = stacked_bar_ordinal(dem["financial"], TITLE, n, height=180, mode=palette_mode, alt_config=alt_config,
                                        grouper=grouper, group_order=group_order)
    fig_methods = horizontal_bar_ranked(
        rec["rec_methods"], "label", "count",
        "Top recruitment methods used", n, max_items=6, height=300,
    )
    fig_rec_barriers = horizontal_bar_ranked(
        rec["rec_barriers"], "label", "count",
        "Top barriers to volunteer recruitment", n, max_items=6, height=300,
    )
    fig_ret_barriers = horizontal_bar_ranked(
        ret["ret_barriers"], "label", "count",
        "Top barriers to volunteer retention", n, max_items=6, height=300,
    )
    fig_concerns = horizontal_bar_ranked(
        wf["concerns"], "label", "count",
        "Top organisational concerns", n, max_items=6, height=300,
    )
    fig_shortage = horizontal_bar_ranked(
        wf["shortage_affect"], "label", "count",
        "Impact of shortages on operations", n, max_items=6, height=300,
    )

    grouper_ed, group_order_ed = resolve_grouping(EXPECT_DEMAND_ORDER)
    fig_expect_demand = stacked_bar_ordinal(
        dem["expect_demand"], "Expected demand (next 3 months)", n, height=180,
        mode=palette_mode, alt_config=alt_config,
        grouper=grouper_ed, group_order=group_order_ed,
    )
    grouper_ef, group_order_ef = resolve_grouping(EXPECT_FINANCIAL_ORDER)
    fig_expect_financial = stacked_bar_ordinal(
        dem["expect_financial"], "Expected financial position (next 3 months)", n, height=180,
        mode=palette_mode, alt_config=alt_config,
        grouper=grouper_ef, group_order=group_order_ef,
    )

    # Simple infographic-style bar chart for top-level metrics
    infographic_data = [
        ("Demand increased", dem["demand_pct_increased"]),
        ("Finances deteriorated", dem["financial_pct_deteriorated"]),
        ("Too few volunteers", rec["pct_too_few"]),
        ("Recruitment difficult", rec["pct_difficulty"]),
        ("Retention difficult", ret["pct_difficulty"]),
    ]
    info_df = pd.DataFrame(infographic_data, columns=["Metric", "Percent"])
    fig_infographic = horizontal_bar_ranked(
        info_df,
        label_col="Metric",
        value_col="Percent",
        pct_col="Percent",
        title="At-a-Glance: Key Pressures on the Voluntary Sector",
        n=n,
        max_items=8,
        height=320,
    )
    # Ensure clear alt text for the infographic slide
    setattr(
        fig_infographic,
        "_alt_text",
        "Horizontal bar chart showing key percentages for demand, finances, "
        "volunteer availability, and recruitment and retention difficulty.",
    )

    slides = [
        {
            "title": "Baromedr Cymru Wave 2",
            "subtitle": "Volunteering in the Welsh Voluntary Sector",
            "body": f"Analysis of {n} voluntary sector organisations<br>"
                    f"Wave 2 survey period: January–February 2026<br>"
                    f"Prepared {date.today().strftime('%B %Y')}",
            "chart": None,
            "notes": "Title slide. Introduce the survey and scope.",
            "alt_text": "",
        },
        {
            "title": "Executive Summary - Key Highlights",
            "subtitle": f"Baromedr Cymru Wave 2 Key Findings: Volunteering in the Welsh Voluntary Sector ({n} organisations across Wales)",
            "body": (
                highlights_html
                + "<p style='font-size:0.8em;color:#555'>These findings are based on an "
                  "organisational survey. Headline estimates of how many people in Wales "
                  "volunteer (for example, that around one-third of adults volunteer) "
                  "depend on survey definitions, age ranges, and whether unpaid caring is "
                  "included. Future waves could triangulate these organisational views "
                  "with surveys of individual volunteers and non-volunteers.</p>"
            ),
            "chart": None,
            "notes": "Top-ranked findings from the survey.",
            "alt_text": "Ordered list of key survey highlights, ranked from most to least important.",
            "is_exec_summary": True,
        },
        {
            "title": "At-a-Glance Infographic",
            "subtitle": "Key pressures on demand, finance and volunteering",
            "body": (
                "<p>High-level indicators summarising the squeeze between "
                "rising demand, constrained finances, and volunteer gaps.</p>"
                f"<p><strong>{n}</strong> organisations in view | "
                f"<strong>{dem['demand_pct_increased']}%</strong> demand increased ▲ | "
                f"<strong>{dem['financial_pct_deteriorated']}%</strong> finances deteriorated ▼ | "
                f"<strong>{rec['pct_too_few']}%</strong> too few volunteers ▼ | "
                f"<strong>{rec['pct_difficulty']}%</strong> recruitment difficult ▼ | "
                f"<strong>{ret['pct_difficulty']}%</strong> retention difficult ▼</p>"
            ),
            "chart": fig_infographic,
            "notes": "Infographic-style slide to open conversations with senior stakeholders.",
            "alt_text": getattr(fig_infographic, "_alt_text", ""),
        },
        {
            "title": "Who Responded?",
            "subtitle": f"{n} organisations across Wales",
            "body": (
                f"<p>Respondents include a mix of small, medium and large organisations "
                f"(Small {prof['org_size'].get('Small', 0)}, Medium {prof['org_size'].get('Medium', 0)}, "
                f"Large {prof['org_size'].get('Large', 0)}). "
                f"{prof['social_enterprise_pct']}% are social enterprises and {prof['has_paid_staff_pct']}% have paid staff; "
                f"median volunteers per organisation is {prof['median_volunteers']:.0f}.</p>"
            ),
            "chart": fig_size,
            "notes": "Sample composition. Emphasise mix of sizes.",
            "alt_text": getattr(fig_size, "_alt_text", ""),
        },
        {
            "title": "Demand Is Rising, Finances Are Flat",
            "subtitle": "The scissor effect",
            "body": f"<ul>"
                    f"<li><strong>{dem['demand_pct_increased']}%</strong> report increased demand</li> <br>"
                    f"<li><strong>{dem['financial_pct_deteriorated']}%</strong> report deteriorating finances</li> <br>"
                    f"<li><strong>{dem['operating_pct_likely']}%</strong> confident they'll operate next year</li> <br>"
                    f"</ul>"
                    f"<p>{demand_finance_scissor_phrase(dem)}</p>"
                    f"<p style='font-size:0.7em;color:#888'>Wave 1 context: "
                    f"{WAVE1_CONTEXT.demand_increased_callout()}</p>",
            "chart": fig_demand,
            "notes": "Demand-finance divergence. Wave 1 comparison available.",
            "alt_text": getattr(fig_demand, "_alt_text", ""),
        },
        {
            "title": "Finances mostly unchanged, but a third report deterioration",
            "subtitle": "Multi-point squeeze on financial stability",
            "body": f"<ul>"
                    f"<li><strong>{dem['financial_pct_deteriorated']}%</strong> already report deteriorating finances</li> <br>"
                    f"<li><strong>{wf['finance_deteriorated_pct']}%</strong> say finances worsened due to rising costs</li> <br>"
                    f"<li>Only {wf['reserves_yes_pct']}% have reserves; median {wf['median_months_reserves']:.0f} months</li> <br>"
                    f"</ul>"
                    f"<p style='font-size:0.7em;color:#888'>Wave 1 context: "
                    f"{WAVE1_CONTEXT.financial_deteriorated_callout()}</p>",
            "chart": fig_financial,
            "notes": "Financial position squeeze. Reserves runway is shrinking.",
            "alt_text": getattr(fig_financial, "_alt_text", ""),
        },
        {
            "title": "Looking Ahead: The Outlook Is Not Improving",
            "subtitle": "Expectations for the next 3 months",
            "body": f"<ul>"
                    f"<li>Organisations expect demand to continue rising</li> <br>"
                    f"<li>Few expect financial improvement</li> <br>"
                    f"<li>The scissor effect is expected to widen, not close</li> <br>"
                    f"</ul>",
            "chart": fig_expect_demand,
            "notes": "Forward-looking data. Policy intervention needed before next wave.",
            "alt_text": getattr(fig_expect_demand, "_alt_text", ""),
        },
        {
            "title": f"The Volunteer Gap: {rec['pct_too_few']}% Say Too Few",
            "subtitle": "Recruitment is the bigger challenge",
            "body": (
                f"<ul>"
                f"<li><strong>{rec['pct_difficulty']}%</strong> report difficulty recruiting</li> <br>"
                f"<li><strong>{ret['pct_difficulty']}%</strong> report difficulty retaining</li> <br>"
                f"<li>{recruitment_vs_retention_phrase(rec, ret)}</li>"
                + (f" <br><li>Among organisations with deteriorating finances, <strong>{cross['pct_rec_difficulty_if_finance_deteriorated']}%</strong> find recruitment difficult, vs <strong>{cross['pct_rec_difficulty_if_finance_not_deteriorated']}%</strong> where finances have not deteriorated.</li>" if cross else "")
                + f"</ul>"
            ),
            "chart": None,
            "notes": "Frame the recruitment/retention asymmetry.",
            "alt_text": "",
        },
        {
            "title": "Recruitment: What Works, What Blocks",
            "subtitle": "Effort is high, but response is low",
            "body": f"<p><strong>Top method</strong>: {rec['rec_methods'].iloc[0]['label']} <br>"
                    f"({rec['rec_methods'].iloc[0]['count']} orgs)</p> <br>"
                    f"<p><strong>Top barrier</strong>: {rec['rec_barriers'].iloc[0]['label']} <br>"
                    f"({rec['rec_barriers'].iloc[0]['count']} orgs)</p> <br>"
                    f"<p>Low response to recruitment campaigns underlines why triangulation with "
                    f"surveys of individual volunteers and non-volunteers would be valuable.</p> <br>",
            "chart": fig_rec_barriers,
            "notes": "Organisations are trying multiple channels. The barrier isn't apathy. It's response rate.",
            "alt_text": getattr(fig_rec_barriers, "_alt_text", ""),
        },
        {
            "title": "Retention: Why Volunteers Leave",
            "subtitle": "Mostly external factors. Not dissatisfaction",
            "body": f"<p><strong>Top barrier</strong>: {ret['ret_barriers'].iloc[0]['label']} <br>"
                    f"({ret['ret_barriers'].iloc[0]['count']} orgs)</p> <br>"
                    f"<p>Work/study changes, caring responsibilities, and natural endings dominate. <br>"
                    f"Factors largely outside organisational control.</p> <br>",
            "chart": fig_ret_barriers,
            "notes": "Good news: orgs aren't driving volunteers away. Bad news: they can't prevent the causes.",
            "alt_text": getattr(fig_ret_barriers, "_alt_text", ""),
        },
        {
            "title": "What Organisations Are Doing (and Need)",
            "subtitle": "Rising costs are forcing hard choices",
            "body": f"<ul>"
                    f"<li><strong>{wf['finance_deteriorated_pct']}%</strong> report finances deteriorated from rising costs</li> <br>"
                    f"<li>Only {wf['reserves_yes_pct']}% have reserves; median "
                    f"{wf['median_months_reserves']:.0f} months of cover among those with reserves</li> <br>"
                    f"</ul>",
            "chart": fig_concerns,
            "notes": "Financial sustainability is the underpinning risk.",
            "alt_text": getattr(fig_concerns, "_alt_text", ""),
        },
        {
            "title": "Impact of Shortages on Operations",
            "subtitle": "Shortages are not abstract; they cause real operational harm",
            "body": f"<ul>"
                    f"<li>Top consequence: {wf['shortage_affect'].iloc[0]['label']} ({wf['shortage_affect'].iloc[0]['count']} orgs)</li> <br>"
                    f"<li>Organisations are stretching existing staff and volunteers to cover gaps</li> <br>"
                    f"</ul>",
            "chart": fig_shortage,
            "notes": "Operational consequences of workforce and volunteer shortages.",
            "alt_text": getattr(fig_shortage, "_alt_text", ""),
        },
        {
            "title": "Earned Settlement: Opportunity or Mandate?",
            "subtitle": "Cautious optimism, but capacity is a concern",
            "body": _earned_settlement_body(vt),
            "chart": None,
            "notes": "Policy opportunity, but requires investment in support infrastructure.",
            "alt_text": "",
        },
        {
            "title": "Recommendations for WCVA Policy Team",
            "subtitle": "Data-grounded next steps",
            "body": "<ol>"
                    "<li>Invest in centralised recruitment campaigns via TSSW/CVCs</li> <br>"
                    "<li>Address the cost-of-living barrier for volunteers (expenses + signposting)</li> <br>"
                    "<li>Promote flexible/micro/remote volunteering models for retention</li> <br>"
                    "<li>Develop early guidance and resource packages for earned settlement</li> <br>"
                    "<li>Monitor the demand–capacity divergence quarterly via Baromedr tracking</li> <br>"
                    "</ol>",
            "chart": None,
            "notes": "Actionable recommendations. Each grounded in data from earlier slides.",
            "alt_text": "",
        },
        {
            "title": "Questions & Next Steps",
            "subtitle": "",
            "body": f"<p>Full interactive dashboard: <code>streamlit run src/app.py</code></p> <br>"
                    f"<p>Dataset: {n} organisations, 162 variables</p> <br>"
                    f"<p>Source: Baromedr Cymru Wave 2, NTU VCSE Observatory / WCVA</p> <br>",
            "chart": None,
            "notes": "Close. Invite questions. Point to dashboard for deep-dives.",
            "alt_text": "",
        },
    ]
    return slides


def _earned_settlement_body(vt: dict) -> str:
    es = vt["earned_settlement"]
    agree = es[es["value"].str.contains("agree", case=False) & ~es["value"].str.contains("disagree", case=False)]["count"].sum()
    disagree = es[es["value"].str.contains("disagree", case=False)]["count"].sum()
    cap = vt["settlement_capacity"]
    return (
        f"<ul>"
        f"<li><strong>{agree}</strong> organisations agree/strongly agree with the principle</li> <br>"
        f"<li><strong>{disagree}</strong> disagree/strongly disagree</li> <br>"
        f"<li>But capacity remains a concern. Many would need additional resources/guidance</li> <br>"
        f"</ul>"
    )


# ---------------------------------------------------------------------------
# Output 1: reveal.js HTML
# ---------------------------------------------------------------------------

REVEAL_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Baromedr Cymru Wave 2 — Executive Presentation</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css">
<style>
  :root {{
    --r-heading-color: {navy};
    --r-main-color: {navy};
    --r-link-color: {teal};
  }}
  .reveal h1, .reveal h2 {{ color: {navy}; }}
  .reveal h3 {{ color: {teal}; font-size: 0.9em; }}
  .reveal .slides section {{
    height: 100% !important;
    box-sizing: border-box;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 20px;
  }}
  .reveal .slide-content {{ text-align: left; padding: 0 40px 20px 40px; }}
  .reveal img.chart {{ max-height: 42vh; max-width: 100%; margin: 10px auto; display: block; border-radius: 4px; }}
  .reveal .subtitle {{ color: {teal}; font-size: 0.75em; margin-top: -10px; }}
  .reveal ul, .reveal ol {{ font-size: 0.75em; line-height: 1.5; }}
  .reveal .footer {{ position: fixed; bottom: 12px; left: 20px; font-size: 0.55em; color: #999; }}
</style>
</head>
<body>
<div class="reveal">
<div class="slides">
{slides_html}
</div>
<div class="footer">Baromedr Cymru Wave 2 | WCVA | {date}</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script>Reveal.initialize({{ hash: true, slideNumber: true, width: 1600, height: 1000, margin: 0.04, minScale: 0.8, maxScale: 1.0 }});</script>
</body>
</html>"""


def generate_html(slides: list[dict]) -> str:
    sections = []
    for s in slides:
        chart_html = ""
        if s["chart"] is not None:
            b64 = _fig_to_base64(s["chart"], width=800, height=380)
            alt = s.get("alt_text", "")
            chart_html = f'<img class="chart" src="data:image/png;base64,{b64}" alt="{alt}">'

        subtitle = f'<h3 class="subtitle">{s["subtitle"]}</h3>' if s["subtitle"] else ""

        section = (
            f'<section>\n'
            f'  <h2>{s["title"]}</h2>\n'
            f'  {subtitle}\n'
            f'  <div class="slide-content">{s["body"]}</div>\n'
            f'  {chart_html}\n'
            f'</section>'
        )
        sections.append(section)

    return REVEAL_TEMPLATE.format(
        slides_html="\n".join(sections),
        navy=WCVA_BRAND["navy"],
        teal=WCVA_BRAND["teal"],
        date=date.today().strftime("%B %Y"),
    )


# ---------------------------------------------------------------------------
# Output 2: Structured PDF via fpdf2
# ---------------------------------------------------------------------------

_NAVY_RGB = tuple(int(WCVA_BRAND["navy"][i:i+2], 16) for i in (1, 3, 5))
_TEAL_RGB = tuple(int(WCVA_BRAND["teal"][i:i+2], 16) for i in (1, 3, 5))
_CORAL_RGB = tuple(int(WCVA_BRAND["coral"][i:i+2], 16) for i in (1, 3, 5))
_AMBER_RGB = tuple(int(WCVA_BRAND["amber"][i:i+2], 16) for i in (1, 3, 5))

_SEVERITY_RGB = {
    "critical": _CORAL_RGB,
    "warning": _AMBER_RGB,
    "neutral": (74, 144, 217),
    "positive": _TEAL_RGB,
}


class BaromedrPDF(FPDF):
    """Custom PDF with WCVA branding, TOC, and bookmarks."""

    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, "Baromedr Cymru Wave 2 | WCVA", align="L")
        self.cell(0, 6, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(10, 14, self.w - 10, 14)
        self.ln(4)

    def footer(self):
        pass

    def add_slide_page(self, title: str, body: str,
                       chart_bytes: bytes | None = None, alt_text: str = "",
                       is_exec_summary: bool = False,
                       highlights: list[dict] | None = None):
        self.add_page()
        self.start_section(title)

        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*_NAVY_RGB)
        self.cell(0, 14, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        if is_exec_summary and highlights:
            self._render_exec_highlights(highlights)
        else:
            self.set_font("Helvetica", "", 11)
            self.set_text_color(50, 50, 50)
            clean_body = _strip_html(body)
            self.multi_cell(0, 6, clean_body)
        self.ln(3)

        if chart_bytes:
            img = io.BytesIO(chart_bytes)
            available_h = self.h - self.get_y() - 20
            if available_h < 60:
                self.add_page()
                available_h = self.h - self.get_y() - 20
            img_h = min(available_h, 120)
            self.image(img, x=20, w=250, h=img_h)
            if alt_text:
                self.ln(2)
                self.set_font("Helvetica", "I", 7)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 4, f"[Alt text: {alt_text}]")

    def _render_exec_highlights(self, highlights: list[dict]):
        """Render executive summary with visual hierarchy."""
        for h in sorted(highlights, key=lambda x: x.get("rank", 0)):
            severity = h.get("type", "neutral")
            rgb = _SEVERITY_RGB.get(severity, _NAVY_RGB)

            y_start = self.get_y()
            x_start = self.l_margin

            self.set_x(x_start + 5)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*rgb)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 8, 6,
                            f"#{h['rank']}: {_strip_html(h['title'])}")

            self.set_x(x_start + 5)
            self.set_font("Helvetica", "", 10)
            self.set_text_color(80, 80, 80)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 8, 5,
                            _strip_html(h["detail"]))

            y_end = self.get_y()
            self.line(x_start + 1, y_start, x_start + 1, y_end)
            self.set_draw_color(*rgb)
            self.set_line_width(0.8)
            self.line(x_start + 1, y_start, x_start + 1, y_end)
            self.set_draw_color(0, 0, 0)
            self.set_line_width(0.2)

            self.ln(3)


def _strip_html(text: str) -> str:
    """Crude HTML tag removal for PDF body text, with Unicode normalisation."""
    import re
    from html import unescape
    text = unescape(text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<li>", "  - ", text)
    text = re.sub(r"</?(ul|ol|li|p|strong|em|code|div|span|h\d)[^>]*>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2022", "-").replace("\u2026", "...")
    # Normalise non-Latin symbols that are not supported by the core Helvetica font
    # used by fpdf2, to avoid Unicode encoding errors during PDF generation.
    text = text.replace("▲", " [up] ").replace("▼", " [down] ")
    return text.strip()


def _render_toc(pdf, outline):
    """Callback for fpdf2's insert_toc_placeholder."""
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*_NAVY_RGB)
    # Title for the TOC page, then spacing so the first entry
    # sits comfortably below the header rule.
    pdf.cell(0, 10, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)

    # Reserve a narrow right-hand column for the page number to avoid
    # collisions or wrapping. The left cell holds the (possibly truncated)
    # section title with indentation.
    page_col_w = 20
    max_title_chars = 80
    line_h = 8
    usable_bottom = pdf.h - pdf.b_margin

    for section in outline:
        # Manual page break for the TOC to ensure that entries
        # never collide with the header on a new page.
        if pdf.get_y() + line_h > usable_bottom:
            pdf.add_page()
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.ln(12)
        indent = "  " * section.level
        name = section.name or ""
        if len(name) > max_title_chars:
            name = name[: max_title_chars - 1] + "…"
        title = f"{indent}{name}"

        # Width available for the title cell within page margins.
        title_w = pdf.w - pdf.l_margin - pdf.r_margin - page_col_w
        pdf.set_x(pdf.l_margin)
        pdf.cell(title_w, 8, title, align="L")
        pdf.cell(page_col_w, 8, str(section.page_number), align="R",
                 new_x="LMARGIN", new_y="NEXT")


def generate_pdf(slides: list[dict], highlights: list[dict] | None = None) -> bytes:
    pdf = BaromedrPDF()
    pdf.set_title("Baromedr Cymru Wave 2 - Executive Presentation")
    pdf.set_author("Bharadwaj Raman - https://github.com/nba1990/")

    first = True
    for s in slides:
        chart_bytes = None
        if s["chart"] is not None:
            chart_bytes = _fig_to_bytes(s["chart"])

        body = s["body"]
        if s["subtitle"]:
            body = f"{s['subtitle']}\n\n{body}"

        is_exec = s.get("is_exec_summary", False)

        if first:
            pdf.add_slide_page(s["title"], body, chart_bytes, s.get("alt_text", ""))
            pdf.insert_toc_placeholder(_render_toc, pages=2)
            first = False
        else:
            pdf.add_slide_page(
                s["title"], body, chart_bytes, s.get("alt_text", ""),
                is_exec_summary=is_exec,
                highlights=highlights if is_exec else None,
            )

    return pdf.output()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data...")
    df = load_dataset()
    print(f"Building slides for {len(df)} organisations...")
    palette_mode = "brand"
    slides = build_slides(df, palette_mode)
    highlights = executive_highlights(df)

    html_path = OUTPUT_DIR / "presentation.html"
    html_content = generate_html(slides)
    html_path.write_text(html_content, encoding="utf-8")
    print(f"HTML presentation: {html_path}")

    pdf_path = OUTPUT_DIR / "presentation.pdf"
    pdf_bytes = generate_pdf(slides, highlights=highlights)
    pdf_path.write_bytes(pdf_bytes)
    print(f"PDF presentation:  {pdf_path}")

    print("Done.")


if __name__ == "__main__":
    main()
