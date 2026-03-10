from __future__ import annotations

from textwrap import dedent
from typing import Mapping, Tuple

import streamlit.components.v1 as components

from src.config import WCVA_BRAND


# -----------------------------------------------------------------------------
# Helper utilities for dynamic colours and trend arrows
# -----------------------------------------------------------------------------

def _compute_trend(
    current: float | None,
    previous: float | None,
    *,
    higher_is_good: bool,
) -> Tuple[str, str]:
    """
    Derive a trend symbol and CSS class from the direction of change.

    - If previous is missing, we keep things neutral (no arrow, grey dot).
    - For "good" metrics (higher_is_good=True) an increase is positive.
    - For "risk" metrics (higher_is_good=False) an increase is negative.
    """
    if current is None or previous is None:
        return "●", "wcva-trend-neutral"

    delta = current - previous
    if abs(delta) < 0.1:
        return "●", "wcva-trend-neutral"

    went_up = delta > 0
    is_positive_change = went_up if higher_is_good else not went_up

    if is_positive_change:
        return "▲", "wcva-trend-up"
    else:
        return "▼", "wcva-trend-down"


def _classify_severity(
    value: float | None,
    *,
    higher_is_good: bool,
) -> str:
    """
    Classify a percentage into 'positive', 'mixed', or 'concerning'.

    Thresholds are intentionally simple so that the story is easy to explain:
    - For "good" metrics (higher_is_good=True):
      70%+ positive, 40–69% mixed, below 40% concerning.
    - For "risk" metrics (higher_is_good=False):
      0–30% positive (low risk), 31–60% mixed, 61%+ concerning.
    """
    if value is None:
        return "mixed"

    if higher_is_good:
        if value >= 70:
            return "positive"
        if value >= 40:
            return "mixed"
        return "concerning"
    else:
        if value <= 30:
            return "positive"
        if value <= 60:
            return "mixed"
        return "concerning"


def _compute_gauge_colour(
    value: float | None,
    *,
    higher_is_good: bool,
) -> str:
    """
    Map a percentage value onto the WCVA palette, taking into account whether
    a high value is reassuring or concerning.

    The thresholds are intentionally simple and centralised so that:
    - 0–39%: poor outcome
    - 40–69%: mixed/amber
    - 70%+: strong outcome
    are flipped for "risk" style metrics where higher values are bad.
    """
    severity = _classify_severity(value, higher_is_good=higher_is_good)
    if severity == "positive":
        return WCVA_BRAND["teal"]
    if severity == "concerning":
        return WCVA_BRAND["coral"]
    return WCVA_BRAND["amber"]


def _build_metrics(n: int, dem: Mapping, rec: Mapping, ret: Mapping) -> list[dict]:
    """
    Return a list of metric definitions for the infographic cards.

    This function is intentionally "data first":
    - Arrows and colours are derived from current vs previous values.
    - Each metric declares whether a higher percentage is reassuring or
      concerning so that colour semantics remain intuitive.

    It remains backwards‑compatible: if no previous values are supplied the
    cards fall back to a neutral trend indicator.
    """
    # Pull out current and (optional) previous values once, to keep the metric
    # definitions below declarative and easy to tweak.
    demand_now = float(dem["demand_pct_increased"])
    demand_prev = float(dem.get("demand_pct_increased_prev", demand_now))

    finance_now = float(dem["financial_pct_deteriorated"])
    finance_prev = float(dem.get("financial_pct_deteriorated_prev", finance_now))

    too_few_now = float(rec["pct_too_few"])
    too_few_prev = float(rec.get("pct_too_few_prev", too_few_now))

    rec_diff_now = float(rec["pct_difficulty"])
    rec_diff_prev = float(rec.get("pct_difficulty_prev", rec_diff_now))

    ret_diff_now = float(ret["pct_difficulty"])
    ret_diff_prev = float(ret.get("pct_difficulty_prev", ret_diff_now))

    # Demand: higher proportion reporting increased demand is *concerning* for
    # capacity, so higher_is_good=False.
    demand_trend_symbol, demand_trend_class = _compute_trend(
        demand_now, demand_prev, higher_is_good=False
    )
    demand_colour = _compute_gauge_colour(demand_now, higher_is_good=False)

    # Finances deteriorated: clearly a risk metric.
    finance_trend_symbol, finance_trend_class = _compute_trend(
        finance_now, finance_prev, higher_is_good=False
    )
    finance_colour = _compute_gauge_colour(finance_now, higher_is_good=False)

    # Too few volunteers: higher percentages are worrying.
    too_few_trend_symbol, too_few_trend_class = _compute_trend(
        too_few_now, too_few_prev, higher_is_good=False
    )
    too_few_colour = _compute_gauge_colour(too_few_now, higher_is_good=False)

    # Recruitment difficulty: higher shares struggling are bad.
    rec_trend_symbol, rec_trend_class = _compute_trend(
        rec_diff_now, rec_diff_prev, higher_is_good=False
    )
    rec_colour = _compute_gauge_colour(rec_diff_now, higher_is_good=False)

    # Retention difficulty: higher shares struggling are bad.
    ret_trend_symbol, ret_trend_class = _compute_trend(
        ret_diff_now, ret_diff_prev, higher_is_good=False
    )
    ret_colour = _compute_gauge_colour(ret_diff_now, higher_is_good=False)

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
            "gauge_fill": 100,
            "gauge_colour": "#E0E5EC",
            "trend_symbol": "●",
            "trend_class": "wcva-trend-neutral",
        },
        {
            "id": "demand",
            "label": "Demand increased",
            "value": f"{dem['demand_pct_increased']}%",
            "caption": "Report increased demand for their services",
            "icon": "📈",
            "theme": "demand",
            "gauge_fill": demand_now,
            "gauge_colour": demand_colour,
            "trend_symbol": demand_trend_symbol,
            "trend_class": demand_trend_class,
            "severity": _classify_severity(demand_now, higher_is_good=False),
        },
        {
            "id": "finance",
            "label": "Finances deteriorated",
            "value": f"{dem['financial_pct_deteriorated']}%",
            "caption": "Say their financial position has worsened",
            "icon": "💷",
            "theme": "finance",
            "gauge_fill": finance_now,
            "gauge_colour": finance_colour,
            "trend_symbol": finance_trend_symbol,
            "trend_class": finance_trend_class,
            "severity": _classify_severity(finance_now, higher_is_good=False),
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
            "gauge_fill": too_few_now,
            "gauge_colour": too_few_colour,
            "trend_symbol": too_few_trend_symbol,
            "trend_class": too_few_trend_class,
            "severity": _classify_severity(too_few_now, higher_is_good=False),
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
            "gauge_fill": rec_diff_now,
            "gauge_colour": rec_colour,
            "trend_symbol": rec_trend_symbol,
            "trend_class": rec_trend_class,
            "severity": _classify_severity(rec_diff_now, higher_is_good=False),
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
            "gauge_fill": ret_diff_now,
            "gauge_colour": ret_colour,
            "trend_symbol": ret_trend_symbol,
            "trend_class": ret_trend_class,
            "severity": _classify_severity(ret_diff_now, higher_is_good=False),
        },
    ]


def render_at_a_glance_infographic(
    n: int,
    dem: Mapping,
    rec: Mapping,
    ret: Mapping,
    *,
    height: int = 720,
    accessible: bool = False,
) -> None:
    """Render a Canva-inspired card grid infographic as a Streamlit HTML component."""
    metrics = _build_metrics(n, dem, rec, ret)

    # Use on-brand colours but keep text dark on light backgrounds for accessibility
    navy = WCVA_BRAND["navy"]

    if accessible:
        # High-contrast palette aligned with the broader dashboard accessible mode.
        teal = "#009E73"   # teal-green from ACCESSIBLE_SEQUENCE
        coral = "#DC267F"  # magenta
        amber = "#FFB000"  # gold
    else:
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
          .wcva-info-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            font-size: 0.78rem;
            color: #555555;
            margin-top: 4px;
          }}
          .wcva-info-legend span {{
            white-space: nowrap;
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
            font-size: 2.1rem;
            font-weight: 700;
            color: {navy};
            margin: 2px 0 4px 0;
          }}
          .wcva-card-value-row {{
            display: flex;
            align-items: center;
            gap: 8px;
          }}
          .wcva-trend-icon {{
            font-size: 1.2rem;
            font-weight: 800;
            line-height: 1;
          }}
          .wcva-trend-up {{
            color: {amber};
          }}
          .wcva-trend-down {{
            color: {coral};
          }}
          .wcva-trend-neutral {{
            color: #888888;
          }}
          .wcva-card-caption {{
            font-size: 0.8rem;
            color: #555555;
          }}
          .wcva-card-severity {{
            font-size: 0.75rem;
            margin-top: 2px;
            color: #444444;
            font-weight: 500;
          }}
          .wcva-pill-bar {{
            position: relative;
            width: 100%;
            max-width: 140px;
            height: 10px;
            margin-top: 6px;
            border-radius: 999px;
            background: #E8EDF3;
            overflow: hidden;
          }}
          .wcva-pill-fill {{
            position: absolute;
            inset: 0;
            width: calc(var(--wcva-gauge-fill, 0) * 1%);
            max-width: 100%;
            border-radius: inherit;
            background: var(--wcva-gauge-colour, {teal});
          }}
        </style>
        """
    )

    severity_phrases = {
        "positive": "Relatively positive",
        "mixed": "Mixed picture",
        "concerning": "High concern",
    }

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
              <div class="wcva-card-value-row">
                <div class="wcva-card-value">{m['value']}</div>
                <div class="wcva-trend-icon {m.get('trend_class', '')}"
                     aria-hidden="true">{m.get('trend_symbol', '')}</div>
              </div>
              <div class="wcva-pill-bar">
                <div class="wcva-pill-fill"
                     style="--wcva-gauge-fill: {m.get('gauge_fill', 0)}; "
                           "--wcva-gauge-colour: {m.get('gauge_colour', teal)};">
                </div>
              </div>
              <div class="wcva-card-caption">{m['caption']}</div>
              <div class="wcva-card-severity">
                {severity_phrases.get(m.get('severity', ''), '')}
              </div>
            </div>
            """
        )

    html = f"""
    <div class="wcva-info-root">
      <div class="wcva-info-legend">
        <span><strong>Arrows:</strong> ▲ improving, ▼ worsening, ● little change vs previous wave</span>
        <span><strong>Colours:</strong> teal = relatively positive, amber = mixed, coral = high concern</span>
      </div>
      <div class="wcva-info-grid">
        {''.join(card_html_parts)}
      </div>
    </div>
    {css}
    """

    components.html(html, height=height)
