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
from pathlib import Path

from fpdf import FPDF
from html import escape
from typing import Mapping, Sequence

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import load_dataset
from src.config import (
    DEMAND_ORDER, FINANCIAL_ORDER, OUTPUT_DIR, WCVA_BRAND, WAVE1_CONTEXT, AltTextConfig, resolve_grouping,
)
from src.eda import (
    profile_summary, demand_and_outlook, volunteer_recruitment_analysis,
    volunteer_retention_analysis, workforce_operations, volunteering_types,
    executive_highlights,
)
from src.charts import (
    horizontal_bar_ranked, stacked_bar_ordinal, donut_chart,
)


def _fig_to_base64(fig, width: int = 900, height: int = 500) -> str:
    """Export a Plotly figure to a base64-encoded PNG string."""
    img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
    return base64.b64encode(img_bytes).decode()


def _fig_to_bytes(fig, width: int = 900, height: int = 500) -> bytes:
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
            "body": highlights_html,
            "chart": None,
            "notes": "Top-ranked findings from the survey.",
            "alt_text": "Ordered list of key survey highlights, ranked from most to least important.",
        },
        {
            "title": "Who Responded?",
            "subtitle": f"{n} organisations across Wales",
            "body": f"<ul>"
                    f"<li><strong>Small</strong>: {prof['org_size'].get('Small', 0)} | <br>"
                    f"<strong>Medium</strong>: {prof['org_size'].get('Medium', 0)} | <br>"
                    f"<strong>Large</strong>: {prof['org_size'].get('Large', 0)}</li> <br>"
                    f"<li>{prof['social_enterprise_pct']}% are social enterprises</li> <br>"
                    f"<li>{prof['has_paid_staff_pct']}% have paid staff</li> <br>"
                    f"<li>Median {prof['median_volunteers']:.0f} volunteers per organisation</li> <br>"
                    f"</ul>",
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
                    f"<p style='font-size:0.7em;color:#888'>Wave 1 context: {WAVE1_CONTEXT['demand_increased_desc']}</p>",
            "chart": fig_demand,
            "notes": "Demand-finance divergence. Wave 1 comparison available.",
            "alt_text": getattr(fig_demand, "_alt_text", ""),
        },
        {
            "title": "Half report stable finances; a third are deteriorating",
            "subtitle": "Multi-point squeeze on financial stability",
            "body": f"<ul>"
                    f"</ul>"
                    f"<p style='font-size:0.7em;color:#888'>Wave 1 context: {WAVE1_CONTEXT['demand_increased_desc']}</p>",
            "chart": fig_financial,
            "notes": "Demand-finance divergence. Wave 1 comparison available.",
            "alt_text": getattr(fig_financial, "_alt_text", ""),
        },
        {
            "title": f"The Volunteer Gap: {rec['pct_too_few']}% Say Too Few",
            "subtitle": "Recruitment is the bigger challenge",
            "body": f"<ul>"
                    f"<li><strong>{rec['pct_difficulty']}%</strong> report difficulty recruiting</li> <br>"
                    f"<li><strong>{ret['pct_difficulty']}%</strong> report difficulty retaining</li> <br>"
                    f"<li>Recruiting is almost 2x harder than retaining</li> <br>"
                    f"</ul>",
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
                    f"({rec['rec_barriers'].iloc[0]['count']} orgs)</p> <br>",
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
                    f"<li>Top actions: increased prices, unplanned reserves usage, reduced services</li> <br>"
                    f"<li>Only {wf['reserves_yes_pct']}% have reserves; median {wf['median_months_reserves']:.0f} months</li> <br>"
                    f"</ul>",
            "chart": fig_concerns,
            "notes": "Financial sustainability is the underpinning risk.",
            "alt_text": getattr(fig_concerns, "_alt_text", ""),
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
                    f"<p>Dataset: {n} organisations, 144 variables</p> <br>"
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
  .reveal .slide-content {{ text-align: left; padding: 0 40px; }}
  .reveal img.chart {{ max-height: 55vh; margin: 10px auto; display: block; border-radius: 4px; }}
  .reveal .subtitle {{ color: {teal}; font-size: 0.75em; margin-top: -10px; }}
  .reveal ul, .reveal ol {{ font-size: 0.85em; line-height: 1.6; }}
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
<script>Reveal.initialize({{ hash: true, slideNumber: true }});</script>
</body>
</html>"""


def generate_html(slides: list[dict]) -> str:
    sections = []
    for s in slides:
        chart_html = ""
        if s["chart"] is not None:
            b64 = _fig_to_base64(s["chart"], width=850, height=450)
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

class BaromedrPDF(FPDF):
    """Custom PDF with WCVA branding, TOC, and bookmarks."""

    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.toc_entries: list[tuple[str, int]] = []

    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, "Baromedr Cymru Wave 2 | WCVA", align="L")
        self.cell(0, 6, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(10, 14, self.w - 10, 14)
        self.ln(4)

    def footer(self):
        pass

    def add_slide_page(self, title: str, body: str, chart_bytes: bytes | None = None, alt_text: str = ""):
        self.add_page()
        self.toc_entries.append((title, self.page_no()))
        bookmark_id = self.start_section(title)

        # Title
        self.set_font("Helvetica", "B", 22)
        navy = tuple(int(WCVA_BRAND["navy"][i:i+2], 16) for i in (1, 3, 5))
        self.set_text_color(*navy)
        self.cell(0, 14, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        # Body text (strip HTML for PDF)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(50, 50, 50)
        clean_body = _strip_html(body)
        self.multi_cell(0, 7, clean_body)
        self.ln(4)

        # Chart image
        if chart_bytes:
            img_path = io.BytesIO(chart_bytes)
            available_h = self.h - self.get_y() - 25
            if available_h < 50:
                self.add_page()
                available_h = self.h - self.get_y() - 25
            img_h = min(available_h, 90)
            self.image(img_path, x=30, w=230, h=img_h)
            if alt_text:
                self.ln(2)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 5, f"[Alt text: {alt_text}]")

    def build_toc_page(self):
        """Insert a TOC as the second page (after title)."""
        # self.page = 1
        self.add_page()
        self.set_font("Helvetica", "B", 18)
        navy = tuple(int(WCVA_BRAND["navy"][i:i+2], 16) for i in (1, 3, 5))
        self.set_text_color(*navy)
        self.cell(0, 14, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

        self.set_font("Helvetica", "", 12)
        self.set_text_color(50, 50, 50)
        for title, page_num in self.toc_entries:
            self.cell(0, 9, f"  {title} {'.' * 60} {page_num + 1}", new_x="LMARGIN", new_y="NEXT")


def _strip_html(text: str) -> str:
    """Crude HTML tag removal for PDF body text, with Unicode normalisation."""
    import re
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<li>", "  - ", text)
    text = re.sub(r"</?(ul|ol|li|p|strong|em|code|div|span|h\d)[^>]*>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2022", "-").replace("\u2026", "...")
    return text.strip()


def generate_pdf(slides: list[dict]) -> bytes:
    pdf = BaromedrPDF()
    pdf.set_title("Baromedr Cymru Wave 2 — Executive Presentation")
    pdf.set_author("Bharadwaj Raman - https://github.com/nba1990/")
    # fpdf2 sets creation_date automatically from system clock

    for s in slides:
        chart_bytes = None
        if s["chart"] is not None:
            chart_bytes = _fig_to_bytes(s["chart"], width=850, height=450)

        body = s["body"]
        if s["subtitle"]:
            body = f"{s['subtitle']}\n\n{body}"

        pdf.add_slide_page(s["title"], body, chart_bytes, s.get("alt_text", ""))

    pdf.build_toc_page()
    return pdf.output()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data...")
    df = load_dataset()
    print(f"Building slides for {len(df)} organisations...")
    accessible_mode = False
    palette_mode = "accessible" if accessible_mode else "brand"
    slides = build_slides(df, palette_mode)

    # HTML output
    html_path = OUTPUT_DIR / "presentation.html"
    html_content = generate_html(slides)
    html_path.write_text(html_content, encoding="utf-8")
    print(f"HTML presentation: {html_path}")

    # PDF output
    pdf_path = OUTPUT_DIR / "presentation.pdf"
    pdf_bytes = generate_pdf(slides)
    pdf_path.write_bytes(pdf_bytes)
    print(f"PDF presentation:  {pdf_path}")

    print("Done.")


if __name__ == "__main__":
    main()
