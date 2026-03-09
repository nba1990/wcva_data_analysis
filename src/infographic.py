from __future__ import annotations

from textwrap import dedent
from typing import Mapping

import streamlit.components.v1 as components

from src.config import WCVA_BRAND


def _build_metrics(n: int, dem: Mapping, rec: Mapping, ret: Mapping) -> list[dict]:
    """Return a list of metric definitions for the infographic cards."""
    return [
        {
            "id": "orgs",
            "label": "Organisations in view",
            "value": f"{n}",
            "caption": (
                "Respondents in this filtered cut of the dataset"
            ),
            "icon": "🏢",
            "theme": "neutral",
        },
        {
            "id": "demand",
            "label": "Demand increased",
            "value": f"{dem['demand_pct_increased']}%",
            "caption": "Report increased demand for their services",
            "icon": "📈",
            "theme": "demand",
        },
        {
            "id": "finance",
            "label": "Finances deteriorated",
            "value": f"{dem['financial_pct_deteriorated']}%",
            "caption": "Say their financial position has worsened",
            "icon": "💷",
            "theme": "finance",
        },
        {
            "id": "too_few",
            "label": "Too few volunteers",
            "value": f"{rec['pct_too_few']}%",
            "caption": (
                "Say they have too few volunteers for their objectives"
            ),
            "icon": "🙋",
            "theme": "volunteers",
        },
        {
            "id": "rec_diff",
            "label": "Recruitment difficult",
            "value": f"{rec['pct_difficulty']}%",
            "caption": (
                "Find recruiting volunteers somewhat or very difficult"
            ),
            "icon": "🧩",
            "theme": "volunteers",
        },
        {
            "id": "ret_diff",
            "label": "Retention difficult",
            "value": f"{ret['pct_difficulty']}%",
            "caption": (
                "Find retaining volunteers somewhat or very difficult"
            ),
            "icon": "🔄",
            "theme": "volunteers",
        },
    ]


def render_at_a_glance_infographic(n: int, dem: Mapping, rec: Mapping, ret: Mapping, *, height: int = 720) -> None:
    """Render a Canva-inspired card grid infographic as a Streamlit HTML component."""
    metrics = _build_metrics(n, dem, rec, ret)

    # Use on-brand colours but keep text dark on light backgrounds for accessibility
    navy = WCVA_BRAND["navy"]
    teal = WCVA_BRAND["teal"]
    coral = WCVA_BRAND["coral"]
    amber = WCVA_BRAND["amber"]

    css = dedent(
        f"""
        <style>
          .wcva-info-root {{
            width: 100%;
            box-sizing: border-box;
          }}
          .wcva-info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-top: 12px;
          }}
          .wcva-card {{
            background: #FFFFFF;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            border-top: 4px solid {navy};
          }}
          .wcva-card-theme-demand {{
            border-top-color: {amber};
          }}
          .wcva-card-theme-finance {{
            border-top-color: {coral};
          }}
          .wcva-card-theme-volunteers {{
            border-top-color: {teal};
          }}
          .wcva-card-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
          }}
          .wcva-card-icon {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #F3F5F7;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
          }}
          .wcva-card-label {{
            font-size: 0.9rem;
            font-weight: 600;
            color: {navy};
          }}
          .wcva-card-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: {navy};
            margin: 2px 0 4px 0;
          }}
          .wcva-card-caption {{
            font-size: 0.8rem;
            color: #555555;
          }}
        </style>
        """
    )

    card_html_parts: list[str] = []
    for m in metrics:
        theme_class = "wcva-card-theme-" + m["theme"] if m.get("theme") else ""
        card_html_parts.append(
            f"""
            <div class="wcva-card {theme_class}">
              <div class="wcva-card-header">
                <div class="wcva-card-icon" aria-hidden="true">{m.get("icon", "")}</div>
                <div class="wcva-card-label">{m['label']}</div>
              </div>
              <div class="wcva-card-value">{m['value']}</div>
              <div class="wcva-card-caption">{m['caption']}</div>
            </div>
            """
        )

    html = f"""
    <div class="wcva-info-root">
      <div class="wcva-info-grid">
        {''.join(card_html_parts)}
      </div>
    </div>
    {css}
    """

    components.html(html, height=height)
