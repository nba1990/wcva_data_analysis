"""
Central configuration for the Baromedr Cymru Wave 2 analysis.

Provides:
- Paths: PROJECT_ROOT, DATA_DIR, OUTPUT_DIR, DATASET_PATH.
- Constants: K_ANON_THRESHOLD, DEBUG_MEMORY, WCVA_BRAND, palette sequences.
- StreamlitAppUISharedConfigState: Per-session UI state (filters, accessibility).
- AltTextConfig: Chart alt-text generation options.
- Label groupers and orderings: GROUPERS, GROUP_ORDER, ORDER_TO_GROUPING_KEY,
  resolve_grouping, summarise_stacked_categories, format_group_summary,
  make_stacked_bar_alt.
- Column-to-label mappings: CONCERNS_LABELS, ACTIONS_LABELS, REC_METHODS_LABELS,
  etc., used by data_loader and eda.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, TypeVar

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Debug / development flags (configurable via environment)
# ---------------------------------------------------------------------------
# Set WCVA_DEBUG_MEMORY=1 (or true/yes) to show process memory in the sidebar.
DEBUG_MEMORY = os.environ.get("WCVA_DEBUG_MEMORY", "").lower() in (
    "1",
    "true",
    "yes",
)

LabelGrouper = Callable[[str], str]

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "datasets"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATASET_PATH = DATA_DIR / "WCVA_W2_Anonymised_Dataset.csv"

OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# K-anonymity threshold (matches Baromedr dashboard suppression rule)
# ---------------------------------------------------------------------------
K_ANON_THRESHOLD = 5


@dataclass()
class StreamlitAppUISharedConfigState:
    """Per-session UI state (filters, accessibility, suppression).

    Store one instance in st.session_state via get_app_ui_config().
    Do not use a module-level singleton; each session gets its own instance.

    Attributes:
        base_size_n: Number of organisations in current filter (for chart subtitles).
        text_size_mode: "Normal" or "Larger" from sidebar.
        text_scale: Multiplier for chart font sizes (e.g. 1.0 or 1.2).
        accessible_mode: Whether accessible colour palette is selected.
        palette_mode: "brand" or "accessible".
        size_options: Options for org size filter (populated from data).
        selected_size: Current org size filter value.
        scope_options: Options for geographic scope filter.
        selected_scope: Current scope filter value.
        la_scope_options: Options for local authority filter.
        selected_la_scope: Current LA filter value.
        activity_options: Options for main activity filter.
        selected_activity: Current activity filter value.
        paid_staff_options: Options for paid staff filter.
        selected_paid_staff: Current paid staff filter value.
        concern_label_options: Labels for key concerns multiselect.
        selected_concerns: Selected concern labels (multiselect).
        suppressed: True when n < K_ANON_THRESHOLD (suppress small cells).
    """

    base_size_n: int = 0
    text_size_mode: str = ""
    text_scale: float = 0.0
    accessible_mode: bool = False
    palette_mode: str = "brand"
    size_options: list[str] = field(default_factory=list)
    selected_size: str | None = ""
    scope_options: list[str] = field(default_factory=list)
    selected_scope: str | None = ""
    la_scope_options: list[str] = field(default_factory=list)
    selected_la_scope: str | None = ""
    activity_options: list[str] = field(default_factory=list)
    selected_activity: str | None = ""
    paid_staff_options: list[str] = field(default_factory=list)
    selected_paid_staff: str | None = ""
    concern_label_options: list[str] = field(default_factory=list)
    selected_concerns: list[str] = field(default_factory=list)
    suppressed: bool = False


def get_app_ui_config() -> StreamlitAppUISharedConfigState:
    """Return the per-session UI config, creating it in session_state if needed.

    Returns:
        The single StreamlitAppUISharedConfigState instance for this session.
    """
    key = "app_ui_config"
    if key not in st.session_state:
        st.session_state[key] = StreamlitAppUISharedConfigState()
    return st.session_state[key]


# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------

WCVA_BRAND = {
    "navy": "#1B2A4A",
    "teal": "#00857C",
    "coral": "#E4003B",
    "amber": "#F5A623",
    "blue": "#4A90D9",
    "green": "#3DA35D",
    "light_grey": "#F0F2F5",
    "mid_grey": "#8C8C8C",
    "white": "#FFFFFF",
}

BRAND_SEQUENCE = [
    WCVA_BRAND["teal"],
    WCVA_BRAND["coral"],
    WCVA_BRAND["amber"],
    WCVA_BRAND["blue"],
    WCVA_BRAND["navy"],
    WCVA_BRAND["green"],
    WCVA_BRAND["mid_grey"],
]

# IBM colour-blind safe palette (verified for deuteranopia, protanopia, tritanopia)
ACCESSIBLE_SEQUENCE = [
    "#648FFF",  # blue
    "#DC267F",  # magenta
    "#FE6100",  # orange
    "#FFB000",  # gold
    "#785EF0",  # violet
    "#009E73",  # teal-green
    "#999999",  # grey
]

SEVERITY_COLOURS = {
    "positive": WCVA_BRAND["teal"],
    "neutral": WCVA_BRAND["blue"],
    "warning": WCVA_BRAND["amber"],
    "critical": WCVA_BRAND["coral"],
}

LIKERT_POSITIVE_TO_NEGATIVE = [
    WCVA_BRAND["teal"],
    "#66B2A8",
    WCVA_BRAND["mid_grey"],
    "#E8836B",
    WCVA_BRAND["coral"],
    WCVA_BRAND["blue"],  # Don't know
]

LIKERT_ACCESSIBLE = [
    "#648FFF",
    "#99B8FF",
    "#999999",
    "#FF9966",
    "#DC267F",
    "#FFB000",
]


def get_palette(mode: str = "brand") -> list[str]:
    """Return the main colour sequence for charts (brand or accessible).

    Args:
        mode: "brand" (WCVA colours) or "accessible" (colour-blind safe).

    Returns:
        List of hex colour strings for series/segments.
    """
    if mode == "accessible":
        return ACCESSIBLE_SEQUENCE
    return BRAND_SEQUENCE


def get_likert_colours(mode: str = "brand") -> list[str]:
    """Return the Likert-scale colour sequence (positive to negative + Don't know).

    Args:
        mode: "brand" or "accessible".

    Returns:
        List of hex colour strings, one per Likert level.
    """
    if mode == "accessible":
        return LIKERT_ACCESSIBLE
    return LIKERT_POSITIVE_TO_NEGATIVE


def _relative_luminance(hex_colour: str) -> float:
    """Compute WCAG 2.1 relative luminance from a hex colour (#RRGGBB)."""
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    components = []
    for c in (r, g, b):
        components.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * components[0] + 0.7152 * components[1] + 0.0722 * components[2]


def contrast_ratio(fg: str, bg: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two hex colours.

    Args:
        fg: Foreground hex colour (e.g. "#1B2A4A").
        bg: Background hex colour (e.g. "#FFFFFF").

    Returns:
        Ratio in range [1, 21]; ≥4.5 for AA text, ≥3 for large text.
    """
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def validate_palette_contrast(
    palette: list[str], bg: str = "#FFFFFF", min_ratio: float = 3.0
) -> dict[str, float]:
    """Check each palette colour against a background.

    Args:
        palette: List of hex colours to check.
        bg: Background hex colour.
        min_ratio: Minimum contrast ratio (e.g. 3.0 for large text).

    Returns:
        Dict mapping each palette colour to its contrast ratio with bg.
    """
    return {c: round(contrast_ratio(c, bg), 2) for c in palette}


# ---------------------------------------------------------------------------
# Chart defaults
# ---------------------------------------------------------------------------
CHART_FONT = "Arial, Helvetica, sans-serif"
CHART_FONT_SIZE = 14
CHART_TITLE_SIZE = 18
CHART_BG = WCVA_BRAND["white"]
CHART_GRID = "#E0E0E0"
CHART_MARGIN = dict(l=20, r=20, t=60, b=20)

# ---------------------------------------------------------------------------
# Response orderings (for consistent axis ordering in charts)
# ---------------------------------------------------------------------------
DEMAND_ORDER = [
    "Increased a lot",
    "Increased a little",
    "Stayed the same",
    "Decreased a little",
    "Decreased a lot",
    "Don't know",
]

FINANCIAL_ORDER = [
    "Improved a lot",
    "Improved a little",
    "Stayed the same",
    "Deteriorated a little",
    "Deteriorated a lot",
    "Don't know",
]

EXPECT_DEMAND_ORDER = [
    "Increase a lot",
    "Increase a little",
    "Stay the same",
    "Decrease a little",
    "Decrease a lot",
    "Don't know",
]

EXPECT_FINANCIAL_ORDER = [
    "Improve a lot",
    "Improve a little",
    "Stay the same",
    "Deteriorate a little",
    "Deteriorate a lot",
    "Don't know",
]

DIFFICULTY_ORDER = [
    "Extremely easy",
    "Somewhat easy",
    "Neither easy nor difficult",
    "Somewhat difficult",
    "Extremely difficult",
    "Don't know",
]

OPERATING_ORDER = [
    "Very likely",
    "Quite likely",
    "Neither likely nor unlikely",
    "Quite unlikely",
    "Very unlikely",
    "Don't know",
]

VOL_OBJECTIVES_ORDER = [
    "More than enough volunteers",
    "About the right number of volunteers",
    "Slightly too few volunteers",
    "Significantly too few volunteers",
    "Don't know",
]

VOL_TYPEUSE_ORDER = [
    "Featured heavily",
    "Featured to a moderate extent",
    "Featured to a limited extent",
    "Did not feature",
]

EARNED_SETTLEMENT_ORDER = [
    "Strongly agree",
    "Somewhat agree",
    "Neither agree nor disagree",
    "Somewhat disagree",
    "Strongly disagree",
    "Don't know / too early to say",
]

ORG_SIZE_ORDER = ["Small", "Medium", "Large"]

YES_NO_ORDER = ["Yes", "No", "Don't know"]


# ---------------------------------------------------------------------------
# Alt text accessibility text configuration dataclasses and helper functions (for consistency)  # noqa
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AltTextConfig:
    """Configuration dataclass for generating alt-text for charts."""

    value_col: str
    count_col: str
    pct_col: str
    sample_size: int
    chart_type: str = "Stacked bar"
    max_groups: int | None = None
    include_counts: bool = True
    include_percents: bool = True
    drop_zero: bool = True


def normalise_label(value: str) -> str:
    """Normalise a label for consistent grouping and alt-text (strip, lower, curly apostrophes)."""
    return str(value).strip().lower().replace("’", "'").replace("‘", "'")


def make_pattern_grouper(
    rules: list[tuple[str, tuple[str, ...]]],
    *,
    default: str = "Other",
) -> LabelGrouper:
    """Build a label grouper from (target_group, (pattern1, pattern2, ...)) rules.

    Each rule maps labels containing any of the patterns (after normalise_label)
    to the target group. First matching rule wins; unmatched labels return default.

    Args:
        rules: List of (target_group_name, (substring, ...)) for matching.
        default: Return value when no rule matches.

    Returns:
        A callable that maps a label string to a group name.
    """

    def group(label: str) -> str:
        text = normalise_label(label)

        for target, patterns in rules:
            if any(pattern in text for pattern in patterns):
                return target

        return default

    return group


GROUPERS: dict[str, LabelGrouper] = {
    "demand": make_pattern_grouper(
        [
            ("Increased", ("increase", "increased")),
            ("Stayed the same", ("stayed the same", "stay the same", "same")),
            ("Decreased", ("decrease", "decreased")),
            ("Don't know", ("don't know", "dont know", "too early to say", "not sure")),
        ]
    ),
    "financial": make_pattern_grouper(
        [
            ("Improved", ("improve", "improved")),
            ("Stayed the same", ("stayed the same", "stay the same", "same")),
            ("Deteriorated", ("deteriorate", "deteriorated")),
            ("Don't know", ("don't know", "dont know", "too early to say", "not sure")),
        ]
    ),
    "likelihood": make_pattern_grouper(
        [
            ("Likely", ("very likely", "quite likely", "likely")),
            ("Neither likely nor unlikely", ("neither likely nor unlikely",)),
            ("Unlikely", ("quite unlikely", "very unlikely", "unlikely")),
            ("Don't know", ("don't know", "dont know", "not sure")),
        ]
    ),
    "agreement": make_pattern_grouper(
        [
            ("Agree", ("strongly agree", "somewhat agree", "agree")),
            ("Neither agree nor disagree", ("neither agree nor disagree",)),
            ("Disagree", ("somewhat disagree", "strongly disagree", "disagree")),
            ("Don't know", ("don't know", "dont know", "too early to say", "not sure")),
        ]
    ),
    "difficulty": make_pattern_grouper(
        [
            ("Easy", ("extremely easy", "somewhat easy", "easy")),
            ("Neither easy nor difficult", ("neither easy nor difficult",)),
            ("Difficult", ("somewhat difficult", "extremely difficult", "difficult")),
            ("Don't know", ("don't know", "dont know", "not sure")),
        ]
    ),
    "volunteer_sufficiency": make_pattern_grouper(
        [
            ("Enough volunteers", ("more than enough", "about the right number")),
            (
                "Too few volunteers",
                ("slightly too few", "significantly too few", "too few"),
            ),
            ("Don't know", ("don't know", "dont know", "not sure")),
        ]
    ),
    "feature_use": make_pattern_grouper(
        [
            (
                "Featured",
                (
                    "featured heavily",
                    "featured to a moderate extent",
                    "featured to a limited extent",
                ),
            ),  # noqa
            ("Did not feature", ("did not feature",)),
        ]
    ),
    "yes_no": make_pattern_grouper(
        [
            ("Yes", ("yes",)),
            ("No", ("no",)),
            ("Don't know", ("don't know", "dont know", "not sure")),
        ]
    ),
    "org_size": make_pattern_grouper(
        [
            ("Small", ("small",)),
            ("Medium", ("medium",)),
            ("Large", ("large",)),
        ]
    ),
}

GROUP_ORDER: dict[str, list[str]] = {
    "demand": ["Increased", "Stayed the same", "Decreased", "Don't know"],
    "financial": ["Improved", "Stayed the same", "Deteriorated", "Don't know"],
    "likelihood": ["Likely", "Neither likely nor unlikely", "Unlikely", "Don't know"],
    "agreement": ["Agree", "Neither agree nor disagree", "Disagree", "Don't know"],
    "difficulty": ["Easy", "Neither easy nor difficult", "Difficult", "Don't know"],
    "volunteer_sufficiency": ["Enough volunteers", "Too few volunteers", "Don't know"],
    "feature_use": ["Featured", "Did not feature"],
    "yes_no": ["Yes", "No", "Don't know"],
    "org_size": ["Small", "Medium", "Large"],
}

ORDER_TO_GROUPING_KEY: dict[tuple[str, ...], str] = {
    tuple(DEMAND_ORDER): "demand",
    tuple(FINANCIAL_ORDER): "financial",
    tuple(EXPECT_DEMAND_ORDER): "demand",
    tuple(EXPECT_FINANCIAL_ORDER): "financial",
    tuple(DIFFICULTY_ORDER): "difficulty",
    tuple(OPERATING_ORDER): "likelihood",
    tuple(VOL_OBJECTIVES_ORDER): "volunteer_sufficiency",
    tuple(VOL_TYPEUSE_ORDER): "feature_use",
    tuple(EARNED_SETTLEMENT_ORDER): "agreement",
    tuple(ORG_SIZE_ORDER): "org_size",
    tuple(YES_NO_ORDER): "yes_no",
}


def resolve_grouping(
    order: Iterable[str],
) -> tuple[LabelGrouper | None, list[str] | None]:
    """Resolve a response ordering (e.g. DEMAND_ORDER) to a grouper and display order.

    Args:
        order: Ordered list of response values (must match a key in ORDER_TO_GROUPING_KEY).

    Returns:
        (grouper, group_order) or (None, None) if order is not recognised.
    """
    key = ORDER_TO_GROUPING_KEY.get(tuple(order))
    if key is None:
        return None, None
    return GROUPERS[key], GROUP_ORDER.get(key)


def summarise_stacked_categories(
    df: pd.DataFrame,
    *,
    value_col: str,
    count_col: str,
    pct_col: str,
    grouper: LabelGrouper | None = None,
    group_order: list[str] | None = None,
    drop_zero: bool = True,
) -> pd.DataFrame:
    """Collapse chart categories into broader groups for alt-text or display.

    If grouper is provided, value_col is mapped to a group; then counts and pcts
    are summed by group. Optionally drops groups with zero pct and sorts by group_order.

    Args:
        df: DataFrame with value_col, count_col, pct_col.
        value_col: Column of category labels.
        count_col: Column of counts.
        pct_col: Column of percentages.
        grouper: Optional callable mapping label -> group name.
        group_order: Optional display order for groups.
        drop_zero: If True, exclude rows with pct_col == 0.

    Returns:
        DataFrame with columns group, count_col, pct_col (aggregated).
    """
    working = df[[value_col, count_col, pct_col]].copy()

    if grouper is None:
        working["group"] = working[value_col].astype(str)
    else:
        working["group"] = working[value_col].map(grouper)

    grouped = working.groupby("group", as_index=False)[[count_col, pct_col]].sum()

    if drop_zero:
        grouped = grouped[grouped[pct_col] > 0].copy()

    if group_order:
        rank = {name: i for i, name in enumerate(group_order)}
        grouped["_rank"] = grouped["group"].map(lambda x: rank.get(x, len(rank)))
        grouped = grouped.sort_values(["_rank", pct_col], ascending=[True, False]).drop(
            columns="_rank"
        )
    else:
        grouped = grouped.sort_values(pct_col, ascending=False)

    return grouped.reset_index(drop=True)


def format_group_summary(
    grouped: pd.DataFrame,
    *,
    value_col: str = "group",
    count_col: str,
    pct_col: str,
    include_counts: bool = True,
    include_percents: bool = True,
    max_groups: int | None = None,
) -> str:
    """Format grouped response summary as a single string for alt-text.

    Args:
        grouped: DataFrame with value_col, count_col, pct_col.
        value_col: Column holding group labels.
        count_col: Column holding counts.
        pct_col: Column holding percentages.
        include_counts: Include (count) in output.
        include_percents: Include pct in output.
        max_groups: If set, only format this many groups.

    Returns:
        Comma-separated string e.g. "Increased 60.0% (24), Stayed the same 40.0% (16)".
    """
    rows = grouped.itertuples(index=False)

    parts: list[str] = []
    for i, row in enumerate(rows):
        if max_groups is not None and i >= max_groups:
            break

        label = getattr(row, value_col)
        count = getattr(row, count_col)
        pct = getattr(row, pct_col)

        if include_counts and include_percents:
            parts.append(f"{label} {pct:.1f}% ({count})")
        elif include_percents:
            parts.append(f"{label} {pct:.1f}%")
        elif include_counts:
            parts.append(f"{label} ({count})")
        else:
            parts.append(str(label))

    return ", ".join(parts)


def make_stacked_bar_alt(
    df: pd.DataFrame,
    *,
    title: str,
    config: AltTextConfig,
    grouper: LabelGrouper | None = None,
    group_order: list[str] | None = None,
) -> str:
    """Generate accessibility alt-text for a stacked bar chart.

    Uses summarise_stacked_categories and format_group_summary with config options.
    Prefix includes chart_type and title; suffix includes n from config.sample_size.

    Args:
        df: Chart data with config.value_col, count_col, pct_col.
        title: Chart title.
        config: AltTextConfig for columns and sample_size.
        grouper: Optional label grouper.
        group_order: Optional display order.

    Returns:
        Full alt-text string for the chart.
    """
    grouped = summarise_stacked_categories(
        df,
        value_col=config.value_col,
        count_col=config.count_col,
        pct_col=config.pct_col,
        grouper=grouper,
        group_order=group_order,
        drop_zero=config.drop_zero,
    )

    summary = format_group_summary(
        grouped,
        count_col=config.count_col,
        pct_col=config.pct_col,
        include_counts=config.include_counts,
        include_percents=config.include_percents,
        max_groups=config.max_groups,
    )

    return f"{config.chart_type}: {title}. " f"{summary}. n={config.sample_size}."


# ---------------------------------------------------------------------------
# Column-to-question mappings
# ---------------------------------------------------------------------------


COLUMN_LABELS = {
    "legalform": "Legal status",
    "mainactivity": "Main area of work",
    "socialenterprise": "Social enterprise?",
    "paidworkforce": "Has paid staff?",
    "peopleemploy": "Number of employees",
    "peoplevol": "Number of volunteers",
    "location_wales": "Based in Wales?",
    "wales_scope": "Geographic scope",
    "location_la_primary": "Primary local authority",
    "org_size": "Organisation size",
    "demand": "Demand change (last 3 months)",
    "workforce": "Workforce change (last 3 months)",
    "volunteers": "Volunteer numbers change (last 3 months)",
    "financial": "Financial position change (last 3 months)",
    "expectdemand": "Expected demand (next 3 months)",
    "expectworkforce": "Expected workforce (next 3 months)",
    "expectvolunteers": "Expected volunteers (next 3 months)",
    "expectfinancial": "Expected financial position (next 3 months)",
    "op_demand": "Ability to meet demand (next 3 months)",
    "shortage_staff_rec": "Difficulty recruiting staff?",
    "shortage_staff_ret": "Difficulty retaining staff?",
    "shortage_vol_rec": "Difficulty recruiting volunteers?",
    "shortage_vol_ret": "Difficulty retaining volunteers?",
    "operating": "Likely operating next year?",
    "financedeteriorate": "Finances deteriorated from rising costs?",
    "reserves": "Has financial reserves?",
    "usingreserves": "Currently using reserves?",
    "monthsreserves": "Months of reserves remaining",
    "volobjectives": "Volunteer numbers vs. objectives",
    "vol_manager": "Has a volunteer manager?",
    "vol_rec": "Ease of recruiting volunteers",
    "vol_ret": "Ease of retaining volunteers",
    "vol_time": "Change in total volunteer time (12 months)",
    "earnedsettlement": "Volunteering for earned settlement?",
    "settlement_capacity": "Capacity to support earned settlement",
}

# Multi-select column group labels
CONCERNS_LABELS = {
    "concerns_1": "Income",
    "concerns_2": "Energy prices",
    "concerns_3": "Inflation (non-energy)",
    "concerns_4": "Interest rate changes",
    "concerns_5": "Increasing demand",
    "concerns_6": "Decreasing demand",
    "concerns_7": "Volunteer recruitment",
    "concerns_8": "Volunteer retention",
    "concerns_9": "Staff recruitment",
    "concerns_10": "Staff retention",
}

ACTIONS_LABELS = {
    "actions_1": "Reduced services",
    "actions_2": "Increased prices",
    "actions_3": "Redundancies",
    "actions_4": "Reduced staff hours",
    "actions_5": "Increased volunteer responsibilities",
    "actions_6": "Reduced office/workspace",
    "actions_7": "Renegotiated contracts",
    "actions_8": "Cancelled contracts",
    "actions_9": "Sold assets",
    "actions_10": "Unplanned use of reserves",
    "actions_11": "Taken on debt",
    "actions_12": "None of the above",
}

SHORTAGE_AFFECT_LABELS = {
    "shortageaffect_1": "Employees working increased hours",
    "shortageaffect_2": "Volunteers working increased hours",
    "shortageaffect_3": "Paused operations entirely",
    "shortageaffect_4": "Paused some operations",
    "shortageaffect_5": "Recruited temporary workers",
    "shortageaffect_6": "Unable to meet demand",
}

REC_METHODS_LABELS = {
    "vol_recmethods_1": "Casual social media",
    "vol_recmethods_2": "Professional social media (LinkedIn)",
    "vol_recmethods_3": "Own digital channels",
    "vol_recmethods_4": "Recruitment platforms/apps",
    "vol_recmethods_5": "Paid marketing/advertising",
    "vol_recmethods_6": "In-person events/outreach",
    "vol_recmethods_7": "Collaboration with other orgs",
    "vol_recmethods_8": "Local volunteering centre",
    "vol_recmethods_9": "National/regional campaigns",
    "vol_recmethods_10": "Employability referral routes",
    "vol_recmethods_11": "Health/wellbeing referral routes",
    "vol_recmethods_12": "Education/training referral routes",
    "vol_recmethods_13": "Word of mouth/informal networks",
    "vol_recmethods_15": "No methods used (last 12 months)",
}

REC_BARRIERS_LABELS = {
    "vol_recbarriers_1": "Low response to recruitment",
    "vol_recbarriers_2": "Limited org capacity to manage",
    "vol_recbarriers_3": "Limited funding for volunteers",
    "vol_recbarriers_4": "Suitability of applicants",
    "vol_recbarriers_5": "Lengthy/complex onboarding",
    "vol_recbarriers_6": "Limited training opportunities",
    "vol_recbarriers_7": "Limited recognition/reward",
    "vol_recbarriers_8": "Roles lack flexibility",
    "vol_recbarriers_9": "Location/travel barriers",
    "vol_recbarriers_10": "Language barriers",
    "vol_recbarriers_11": "Competition for volunteers",
    "vol_recbarriers_13": "N/A — no difficulties",
}

RET_BARRIERS_LABELS = {
    "vol_retbarriers_1": "Work/study changes",
    "vol_retbarriers_2": "Increased caring responsibilities",
    "vol_retbarriers_3": "Can no longer afford to volunteer",
    "vol_retbarriers_4": "Health/wellbeing decline",
    "vol_retbarriers_5": "Natural end of volunteering",
    "vol_retbarriers_6": "Time commitment too high",
    "vol_retbarriers_7": "Responsibility too high",
    "vol_retbarriers_8": "Location/travel requirements",
    "vol_retbarriers_9": "Limited remote/flexible options",
    "vol_retbarriers_10": "Dissatisfaction with experience",
    "vol_retbarriers_11": "Fewer social connections",
    "vol_retbarriers_12": "Limited org resources to support",
    "vol_retbarriers_14": "N/A — no difficulties",
}

VOL_OFFER_LABELS = {
    "vol_offer_1": "Flexible/remote options",
    "vol_offer_2": "Covering expenses",
    "vol_offer_3": "Financial advice signposting",
    "vol_offer_4": "Training and development",
    "vol_offer_5": "Health/wellbeing support",
    "vol_offer_6": "Recognition and social activities",
    "vol_offer_7": "Formal supervision",
    "vol_offer_8": "Clinical supervision",
    "vol_offer_9": "Welsh language learning",
}

VOL_DEM_LABELS = {
    "vol_dem_1": "Under 13",
    "vol_dem_2": "13–15",
    "vol_dem_3": "16–17",
    "vol_dem_4": "18–25",
    "vol_dem_5": "26–49",
    "vol_dem_6": "50–64",
    "vol_dem_7": "65–74",
    "vol_dem_8": "75+",
    "vol_dem_9": "Disabled volunteers",
    "vol_dem_10": "Ethnic minority volunteers",
    "vol_dem_11": "Employer-supported/corporate",
    "vol_dem_12": "Welsh-language speakers",
}

VOL_DEM_CHANGE_LABELS = {
    "vol_dem_change_1": "Under 13",
    "vol_dem_change_2": "13–15",
    "vol_dem_change_3": "16–17",
    "vol_dem_change_4": "18–25",
    "vol_dem_change_5": "26–49",
    "vol_dem_change_6": "50–64",
    "vol_dem_change_7": "65–74",
    "vol_dem_change_8": "75+",
    "vol_dem_change_9": "Disabled volunteers",
    "vol_dem_change_10": "Ethnic minority volunteers",
    "vol_dem_change_11": "Employer-supported/corporate",
    "vol_dem_change_12": "Welsh-language speakers",
    "vol_dem_change_13": "All volunteers",
}

VOL_TYPEUSE_LABELS = {
    "vol_typeuse_1": "Regular, ongoing roles",
    "vol_typeuse_2": "Ad-hoc or event-based",
    "vol_typeuse_3": "Micro-volunteering",
    "vol_typeuse_4": "Virtual volunteering",
    "vol_typeuse_5": "Remote volunteering",
    "vol_typeuse_6": "Skills-based",
    "vol_typeuse_7": "Corporate/employer-supported",
    "vol_typeuse_8": "Family volunteering",
}

# Convenience grouping of all multi-select label dicts
MULTI_SELECT_GROUPS = {
    "concerns": CONCERNS_LABELS,
    "actions": ACTIONS_LABELS,
    "shortage_affect": SHORTAGE_AFFECT_LABELS,
    "rec_methods": REC_METHODS_LABELS,
    "rec_barriers": REC_BARRIERS_LABELS,
    "ret_barriers": RET_BARRIERS_LABELS,
    "vol_offer": VOL_OFFER_LABELS,
    "vol_dem": VOL_DEM_LABELS,
    "vol_dem_change": VOL_DEM_CHANGE_LABELS,
    "vol_typeuse": VOL_TYPEUSE_LABELS,
}

# ---------------------------------------------------------------------------
# Welsh local authority region mapping
# ---------------------------------------------------------------------------
LA_TO_REGION = {
    "Isle of Anglesey": "North Wales",
    "Gwynedd": "North Wales",
    "Conwy": "North Wales",
    "Denbighshire": "North Wales",
    "Flintshire": "North Wales",
    "Wrexham": "North Wales",
    "Powys": "Mid Wales",
    "Ceredigion": "Mid Wales",
    "Pembrokeshire": "South West Wales",
    "Carmarthenshire": "South West Wales",
    "Swansea": "South West Wales",
    "Neath Port Talbot": "South West Wales",
    "Bridgend": "South Wales",
    "Vale of Glamorgan": "South Wales",
    "Cardiff": "South Wales",
    "Rhondda Cynon Taf": "South Wales",
    "Merthyr Tydfil": "South Wales Valleys",
    "Caerphilly": "South Wales Valleys",
    "Blaenau Gwent": "South Wales Valleys",
    "Torfaen": "South East Wales",
    "Monmouthshire": "South East Wales",
    "Newport": "South East Wales",
}
