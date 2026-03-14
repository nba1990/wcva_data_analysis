"""
Narrative text helpers for the Baromedr dashboard.

Builds human-readable sentences from EDA result dicts (demand_and_outlook,
volunteer_recruitment_analysis, volunteer_retention_analysis) for use in
executive summary, at-a-glance, and similar pages.
"""

from __future__ import annotations

from typing import Mapping


def _safe_pct(mapping: Mapping[str, object], key: str) -> float:
    """Extract a numeric percentage from a mapping, with safe fallbacks.

    Handles missing key (0), non-mapping (AttributeError -> 0), and
    non-numeric values (TypeError/ValueError -> 0.0).

    Args:
        mapping: Dict-like with optional key (e.g. demand_and_outlook result).
        key: Key to look up (e.g. "demand_pct_increased").

    Returns:
        float in [0, 100] or 0.0 on any error.
    """
    try:
        value = mapping.get(key, 0)
    except AttributeError:
        value = 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def demand_finance_scissor_phrase(dem: Mapping[str, object]) -> str:
    """Short narrative about demand vs. finance based on pct metrics.

    Uses dem["demand_pct_increased"] and dem["financial_pct_deteriorated"]
    (via _safe_pct). Mentions "scissor effect" when both are non-zero.

    Args:
        dem: Result of demand_and_outlook() or dict with same keys.

    Returns:
        One or two sentences for display.
    """
    demand_pct = _safe_pct(dem, "demand_pct_increased")
    finance_pct = _safe_pct(dem, "financial_pct_deteriorated")

    if not demand_pct and not finance_pct:
        return "Demand and finances show no clear overall shift in this wave."

    parts: list[str] = []
    if demand_pct:
        parts.append(f"{demand_pct:.1f}% of organisations report increased demand")
    if finance_pct:
        parts.append(
            f"{finance_pct:.1f}% report their finances have deteriorated (last 3 months)"
        )

    core = "; ".join(parts)
    if demand_pct and finance_pct:
        return (
            core + ". Together, this widens the 'scissor effect' between "
            "rising demand and squeezed resources."
        )
    return core + "."


def recruitment_vs_retention_phrase(
    rec: Mapping[str, object], ret: Mapping[str, object]
) -> str:
    """Explain how hard recruitment is relative to retention.

    Uses pct_difficulty from both rec and ret; compares ratio to produce
    "more commonly reported as difficult than", "about as hard as", or
    "somewhat easier than". Handles missing or sparse data with fallback text.

    Args:
        rec: Result of volunteer_recruitment_analysis() (or dict with pct_difficulty).
        ret: Result of volunteer_retention_analysis() (or dict with pct_difficulty).

    Returns:
        One sentence for display.
    """
    rec_pct = _safe_pct(rec, "pct_difficulty")
    ret_pct = _safe_pct(ret, "pct_difficulty")

    # Fallback if we don't have both numbers
    if not rec_pct and not ret_pct:
        return "We have limited comparable data on recruitment and retention difficulty in this cut."
    if rec_pct and not ret_pct:
        return (
            f"{rec_pct:.1f}% report recruitment as somewhat or very "
            "difficult; retention data is too sparse to compare."
        )
    if ret_pct and not rec_pct:
        return (
            f"{ret_pct:.1f}% report retention as somewhat or very "
            "difficult; recruitment data is too sparse to compare."
        )

    ratio = rec_pct / ret_pct if ret_pct else 0

    if ratio >= 1.8:
        comparison = "more commonly reported as difficult than"
    elif ratio >= 1.4:
        comparison = "more commonly reported as difficult than"
    elif ratio >= 1.1:
        comparison = "a bit more commonly reported as difficult than"
    elif ratio >= 0.9:
        comparison = "about as hard as"
    else:
        comparison = "somewhat easier than"

    return (
        "Recruiting volunteers is "
        f"{comparison} retaining them "
        f"({rec_pct:.1f}% vs. {ret_pct:.1f}% reporting difficulty)."
    )
