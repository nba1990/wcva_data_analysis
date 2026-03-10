from __future__ import annotations

from typing import Any, Dict, Mapping

import pandas as pd
from pydantic import BaseModel, Field, ConfigDict

class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


PctField = Field(ge=0, le=100)
CountField = Field(ge=0)


# ============================================================
# Shared schema
# ============================================================

class Meta(StrictBaseModel):
    title: str
    subtitle: str
    wave_label: str
    wave_number: int = Field(ge=1)
    wave_response_count: int = CountField
    wave_response_desc: str


class HeadlineFinancialHealth(StrictBaseModel):
    financial_position_deteriorated_due_to_rising_costs_pct: int = PctField
    using_reserves_to_cover_operational_costs_pct: int = PctField
    has_financial_reserves_pct: int | None = Field(default=None, ge=0, le=100)
    using_reserves_among_those_with_reserves_pct: int | None = Field(default=None, ge=0, le=100)


class HeadlineKPIs(StrictBaseModel):
    financial_health: HeadlineFinancialHealth
    workforce: WorkforceHeadline
    operations: OperationsHeadline


class RankedConcern(StrictBaseModel):
    rank: int = Field(ge=1)
    concern: str
    pct: int = PctField


class KeyOrganisationalConcernsTopCards(StrictBaseModel):
    income_pct: int = PctField
    increasing_demand_for_services_pct: int = PctField
    inflation_goods_and_services_prices_other_than_energy_pct: int = PctField


class KeyOrganisationalConcerns(StrictBaseModel):
    section_title: str
    organisations_answered: int = CountField
    top_cards: KeyOrganisationalConcernsTopCards
    ranked_concerns: list[RankedConcern]


class FinanceHeadline(StrictBaseModel):
    using_reserves_to_cover_operational_costs_pct: int = PctField
    no_reserves_available_pct: int = PctField
    financial_position_deteriorated_due_to_rising_costs_pct: int = PctField


class IncomeBreakdown(StrictBaseModel):
    section_title: str
    organisations_answered: int = CountField
    sources_pct: Dict[str, int]

    def model_post_init(self, __context) -> None:
        for key, value in self.sources_pct.items():
            if not 0 <= value <= 100:
                raise ValueError(f"Income percentage out of range for '{key}': {value}")


class ExpenditureBreakdown(StrictBaseModel):
    section_title: str
    organisations_answered: int = CountField
    categories_pct: Dict[str, int]

    def model_post_init(self, __context) -> None:
        for key, value in self.categories_pct.items():
            if not 0 <= value <= 100:
                raise ValueError(f"Expenditure percentage out of range for '{key}': {value}")


class Likert5Change(StrictBaseModel):
    section_title: str

    improved_a_lot_pct: int | None = Field(default=None, ge=0, le=100)
    improved_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    stayed_the_same_pct: int | None = Field(default=None, ge=0, le=100)
    deteriorated_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    deteriorated_a_lot_pct: int | None = Field(default=None, ge=0, le=100)

    increased_a_lot_pct: int | None = Field(default=None, ge=0, le=100)
    increased_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    decreased_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    decreased_a_lot_pct: int | None = Field(default=None, ge=0, le=100)

    increase_a_lot_pct: int | None = Field(default=None, ge=0, le=100)
    increase_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    stay_the_same_pct: int | None = Field(default=None, ge=0, le=100)
    decrease_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    decrease_a_lot_pct: int | None = Field(default=None, ge=0, le=100)

    improve_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    improve_a_lot_pct: int | None = Field(default=None, ge=0, le=100)
    deteriorate_a_little_pct: int | None = Field(default=None, ge=0, le=100)
    deteriorate_a_lot_pct: int | None = Field(default=None, ge=0, le=100)


class ActionsTakenDueToRisingCosts(StrictBaseModel):
    section_title: str
    organisations_answered: int = CountField
    actions_pct: Dict[str, int]

    def model_post_init(self, __context) -> None:
        for key, value in self.actions_pct.items():
            if not 0 <= value <= 100:
                raise ValueError(f"Action percentage out of range for '{key}': {value}")


class FinanceSection(StrictBaseModel):
    headline: FinanceHeadline
    income_breakdown: IncomeBreakdown
    expenditure_breakdown: ExpenditureBreakdown
    change_past_3_months: Likert5Change
    expected_change_next_3_months: Likert5Change
    actions_taken_due_to_rising_costs: ActionsTakenDueToRisingCosts


class DemandHeadline(StrictBaseModel):
    increasing_demand_for_services_pct: int = PctField
    report_insufficient_capacity_to_meet_demand_next_3_months_pct: int = PctField


class AbilityToMeetDemand(StrictBaseModel):
    section_title: str
    we_expect_to_meet_demand_with_limited_no_spare_capacity_pct: int = PctField
    we_expect_to_almost_meet_demand_pct: int = PctField
    we_expect_to_fall_significantly_short_in_our_ability_to_meet_demand_pct: int = PctField
    we_expect_to_meet_demand_with_significant_spare_capacity_pct: int = PctField


class DemandSection(StrictBaseModel):
    headline: DemandHeadline
    change_past_3_months: Likert5Change
    expected_change_next_3_months: Likert5Change
    ability_to_meet_demand_next_3_months: AbilityToMeetDemand


class WorkforceHeadline(StrictBaseModel):
    has_volunteers_pct: int = PctField
    has_paid_staff_pct: int = PctField
    face_staff_recruitment_difficulties_pct: int = PctField
    face_staff_retention_difficulties_pct: int = PctField
    face_volunteer_recruitment_difficulties_pct: int = PctField
    face_volunteer_retention_difficulties_pct: int = PctField
    too_few_volunteers_pct: int | None = Field(default=None, ge=0, le=100)


class RecruitmentAndRetentionConcerns(StrictBaseModel):
    staff_recruitment_concern_pct: int = PctField
    staff_retention_concern_pct: int = PctField
    volunteer_recruitment_concern_pct: int = PctField
    volunteer_retention_concern_pct: int = PctField


class ImpactOfRecruitmentDifficulties(StrictBaseModel):
    section_title: str
    employees_working_increased_hours_pct: int = PctField
    volunteers_working_increased_hours_pct: int = PctField
    had_to_pause_some_operations_pct: int = PctField
    unable_to_meet_demand_pct: int = PctField
    had_to_recruit_temporary_workers_pct: int = PctField
    other_pct: int = PctField


class WorkforceSection(StrictBaseModel):
    headline: WorkforceHeadline
    recruitment_and_retention_concerns: RecruitmentAndRetentionConcerns
    impact_of_recruitment_difficulties: ImpactOfRecruitmentDifficulties
    change_in_paid_staff_numbers_last_3_months: Likert5Change
    change_in_volunteer_numbers_last_3_months: Likert5Change
    expected_change_in_paid_staff_numbers_next_3_months: Likert5Change
    expected_change_in_volunteer_numbers_next_3_months: Likert5Change


class OperationsHeadline(StrictBaseModel):
    likelihood_of_operating_this_time_next_year_pct: int = PctField
    report_insufficient_capacity_to_meet_demand_next_3_months_pct: int = PctField


class OperationsSection(StrictBaseModel):
    headline: OperationsHeadline


class RespondentProfile(StrictBaseModel):
    section_title: str
    subtitle: str
    responses_by_survey_wave: int = CountField
    main_activities_of_participating_organisations: Dict[str, int]
    organisation_size_by_income_band: Dict[str, int]
    number_of_paid_staff_employed_by_organisations: Dict[str, int]

    def model_post_init(self, __context) -> None:
        groups = {
            "main_activities_of_participating_organisations": self.main_activities_of_participating_organisations,
            "organisation_size_by_income_band": self.organisation_size_by_income_band,
            "number_of_paid_staff_employed_by_organisations": self.number_of_paid_staff_employed_by_organisations,
        }
        for group_name, mapping in groups.items():
            for key, value in mapping.items():
                if not 0 <= value <= 100:
                    raise ValueError(f"Profile percentage out of range for '{group_name}.{key}': {value}")


class WaveContext(StrictBaseModel):
    meta: Meta
    headline_kpis: HeadlineKPIs
    key_organisational_concerns: KeyOrganisationalConcerns
    finance: FinanceSection
    demand: DemandSection
    workforce: WorkforceSection
    operations: OperationsSection
    respondent_profile: RespondentProfile

    # -----------------------------------------------------------------------
    # Narrative helpers for cross-wave callouts
    # -----------------------------------------------------------------------

    def wave_response_callout(self) -> str:
        """
        Short sentence describing the number of organisations that responded
        in this wave (uses the pre-composed meta description where available).
        """
        return self.meta.wave_response_desc

    def staff_recruitment_concern_callout(self) -> str:
        pct = self.workforce.recruitment_and_retention_concerns.staff_recruitment_concern_pct
        return (
            f"{pct}% of {self.meta.wave_label} respondents listed staff recruitment "
            "as a key concern"
        )

    def staff_retention_concern_callout(self) -> str:
        pct = self.workforce.recruitment_and_retention_concerns.staff_retention_concern_pct
        return (
            f"{pct}% of {self.meta.wave_label} respondents listed staff retention "
            "as a key concern"
        )

    def volunteer_recruitment_concern_callout(self) -> str:
        pct = self.workforce.recruitment_and_retention_concerns.volunteer_recruitment_concern_pct
        return (
            f"{pct}% of {self.meta.wave_label} respondents listed volunteer recruitment "
            "as a key concern"
        )

    def volunteer_retention_concern_callout(self) -> str:
        pct = self.workforce.recruitment_and_retention_concerns.volunteer_retention_concern_pct
        return (
            f"{pct}% of {self.meta.wave_label} respondents listed volunteer retention "
            "as a key concern"
        )

    def demand_increased_callout(self) -> str:
        pct = self.demand.headline.increasing_demand_for_services_pct
        return (
            f"{pct}% of {self.meta.wave_label} respondents reported increasing demand "
            "for services"
        )

    def financial_deteriorated_callout(self) -> str:
        pct = self.finance.headline.financial_position_deteriorated_due_to_rising_costs_pct
        return (
            f"{pct}% of organisations reported their financial position deteriorated "
            f"due to rising costs in {self.meta.wave_label}"
        )

    def executive_context_callouts(self) -> list[str]:
        """
        Convenience bundle of key context callouts for dashboards and reports.
        """
        return [
            self.wave_response_callout(),
            self.staff_recruitment_concern_callout(),
            self.staff_retention_concern_callout(),
            self.volunteer_recruitment_concern_callout(),
            self.volunteer_retention_concern_callout(),
            self.demand_increased_callout(),
            self.financial_deteriorated_callout(),
        ]


# ============================================================
# Loader / registry utilities
# ============================================================

class WaveRegistry(StrictBaseModel):
    waves: Dict[str, WaveContext]

    def get(self, wave_label: str) -> WaveContext:
        return self.waves[wave_label]

    def list_waves(self) -> list[str]:
        return sorted(
            self.waves.keys(),
            key=lambda label: self.waves[label].meta.wave_number,
        )


def build_wave_context_from_df(
    df: pd.DataFrame,
    *,
    wave_label: str,
    wave_number: int,
) -> WaveContext:
    """
    Construct a WaveContext from an analysed survey DataFrame.

    This is intended for Wave 2+ where the source is a row-level dataset
    rather than a hand-crafted Wave 1 payload. It uses simple aggregations
    that align with the existing Wave 1 structure.
    """
    from src.eda import (
        demand_and_outlook,
        workforce_operations,
        profile_summary,
        volunteer_recruitment_analysis,
    )

    prof = profile_summary(df)
    dem = demand_and_outlook(df)
    wf = workforce_operations(df)
    rec = volunteer_recruitment_analysis(df)

    n = prof["n"]

    meta = Meta(
        title="Key Performance Indicators",
        subtitle="Organisational survey",
        wave_label=wave_label,
        wave_number=wave_number,
        wave_response_count=n,
        wave_response_desc=f"{n} organisations responded to {wave_label}",
    )

    financial_health = HeadlineFinancialHealth(
        financial_position_deteriorated_due_to_rising_costs_pct=int(round(wf["finance_deteriorated_pct"])),
        using_reserves_to_cover_operational_costs_pct=int(round(wf["using_reserves_pct"])),
        has_financial_reserves_pct=int(round(wf["reserves_yes_pct"])),
        using_reserves_among_those_with_reserves_pct=int(round(wf["using_reserves_pct"])),
    )

    workforce_headline = WorkforceHeadline(
        has_volunteers_pct=int(round(prof["has_volunteers_pct"])),
        has_paid_staff_pct=int(round(prof["has_paid_staff_pct"])),
        face_staff_recruitment_difficulties_pct=int(round(wf["staff_rec_difficulty_pct"])),
        face_staff_retention_difficulties_pct=int(round(wf["staff_ret_difficulty_pct"])),
        face_volunteer_recruitment_difficulties_pct=int(round(wf["vol_rec_difficulty_pct"])),
        face_volunteer_retention_difficulties_pct=int(round(wf["vol_ret_difficulty_pct"])),
        too_few_volunteers_pct=int(round(rec["pct_too_few"])),
    )

    operations_headline = OperationsHeadline(
        likelihood_of_operating_this_time_next_year_pct=int(round(dem["operating_pct_likely"])),
        # Wave 2 does not currently have a direct analogue for this KPI;
        # we default to 0 and can refine once a question is added.
        report_insufficient_capacity_to_meet_demand_next_3_months_pct=0,
    )

    headline_kpis = HeadlineKPIs(
        financial_health=financial_health,
        workforce=workforce_headline,
        operations=operations_headline,
    )

    # Key organisational concerns from multi-select block
    concerns_df = wf["concerns"]
    income_row = concerns_df[concerns_df["label"] == "Income"].iloc[0]
    inc_demand_row = concerns_df[concerns_df["label"].str.contains("Increasing demand", case=False)].iloc[0]
    inflation_row = concerns_df[concerns_df["label"].str.contains("Inflation", case=False)].iloc[0]

    key_concerns_top_cards = KeyOrganisationalConcernsTopCards(
        income_pct=int(round(income_row["pct"])),
        increasing_demand_for_services_pct=int(round(inc_demand_row["pct"])),
        inflation_goods_and_services_prices_other_than_energy_pct=int(round(inflation_row["pct"])),
    )

    ranked_concerns = [
        RankedConcern(rank=i + 1, concern=row["label"], pct=int(round(row["pct"])))
        for i, row in concerns_df.reset_index(drop=True).iterrows()
    ]

    key_organisational_concerns = KeyOrganisationalConcerns(
        section_title="Operational Challenges",
        organisations_answered=n,
        top_cards=key_concerns_top_cards,
        ranked_concerns=ranked_concerns,
    )

    # Demand headline (share saying demand increased)
    demand_headline = DemandHeadline(
        increasing_demand_for_services_pct=int(round(dem["demand_pct_increased"])),
        # There is not currently a direct Wave 2 metric for this exact KPI;
        # we initialise to 0 so that trend analysis still works.
        report_insufficient_capacity_to_meet_demand_next_3_months_pct=0,
    )

    # Minimal demand/workforce/finance/operations sections sufficient for
    # current callouts and comparison helpers. Remaining sub-sections can be
    # populated incrementally as needed.
    demand_section = DemandSection(
        headline=demand_headline,
        change_past_3_months=Likert5Change(section_title="Change in Service Demand Past 3 Months"),
        expected_change_next_3_months=Likert5Change(section_title="Expected Change in Service Demand Over the Next 3 Months"),
        ability_to_meet_demand_next_3_months=AbilityToMeetDemand(
            section_title="Ability to meet demand over the next 3 months",
            we_expect_to_meet_demand_with_limited_no_spare_capacity_pct=0,
            we_expect_to_almost_meet_demand_pct=0,
            we_expect_to_fall_significantly_short_in_our_ability_to_meet_demand_pct=0,
            we_expect_to_meet_demand_with_significant_spare_capacity_pct=0,
        ),
    )

    recruitment_retention = RecruitmentAndRetentionConcerns(
        staff_recruitment_concern_pct=0,
        staff_retention_concern_pct=0,
        volunteer_recruitment_concern_pct=0,
        volunteer_retention_concern_pct=0,
    )

    impact_recruitment = ImpactOfRecruitmentDifficulties(
        section_title="Impact of Recruitment Difficulties",
        employees_working_increased_hours_pct=0,
        volunteers_working_increased_hours_pct=0,
        had_to_pause_some_operations_pct=0,
        unable_to_meet_demand_pct=0,
        had_to_recruit_temporary_workers_pct=0,
        other_pct=0,
    )

    workforce_section = WorkforceSection(
        headline=workforce_headline,
        recruitment_and_retention_concerns=recruitment_retention,
        impact_of_recruitment_difficulties=impact_recruitment,
        change_in_paid_staff_numbers_last_3_months=Likert5Change(
            section_title="Change in Paid Staff Numbers, Last 3 Months"
        ),
        change_in_volunteer_numbers_last_3_months=Likert5Change(
            section_title="Change in Volunteer Numbers, Last 3 Months"
        ),
        expected_change_in_paid_staff_numbers_next_3_months=Likert5Change(
            section_title="Expected Change in Paid Staff Numbers Over the Next 3 Months"
        ),
        expected_change_in_volunteer_numbers_next_3_months=Likert5Change(
            section_title="Expected Change in Volunteer Numbers Over the Next 3 Months"
        ),
    )

    finance_headline = FinanceHeadline(
        using_reserves_to_cover_operational_costs_pct=int(round(wf["using_reserves_pct"])),
        no_reserves_available_pct=0,
        financial_position_deteriorated_due_to_rising_costs_pct=int(round(wf["finance_deteriorated_pct"])),
    )

    income_breakdown = IncomeBreakdown(
        section_title="Breakdown of Income by Funding Source",
        organisations_answered=n,
        sources_pct={},
    )

    expenditure_breakdown = ExpenditureBreakdown(
        section_title="Breakdown of Expenditure by Cost Category",
        organisations_answered=n,
        categories_pct={},
    )

    finance_section = FinanceSection(
        headline=finance_headline,
        income_breakdown=income_breakdown,
        expenditure_breakdown=expenditure_breakdown,
        change_past_3_months=Likert5Change(section_title="Change in financial position past 3 months"),
        expected_change_next_3_months=Likert5Change(
            section_title="Expected Change in Financial Position Over the Next 3 Months"
        ),
        actions_taken_due_to_rising_costs=ActionsTakenDueToRisingCosts(
            section_title="Actions Taken due to Rising Costs",
            organisations_answered=n,
            actions_pct={},
        ),
    )

    operations_section = OperationsSection(
        headline=operations_headline,
    )

    respondent_profile = RespondentProfile(
        section_title="Respondent Profile",
        subtitle="Overview of participating organisations",
        responses_by_survey_wave=n,
        main_activities_of_participating_organisations=prof["mainactivity"],
        organisation_size_by_income_band={},
        number_of_paid_staff_employed_by_organisations={},
    )

    return WaveContext(
        meta=meta,
        headline_kpis=headline_kpis,
        key_organisational_concerns=key_organisational_concerns,
        finance=finance_section,
        demand=demand_section,
        workforce=workforce_section,
        operations=operations_section,
        respondent_profile=respondent_profile,
    )


def load_wave_context(data: Mapping) -> WaveContext:
    """
    Validate and load one wave from a raw dict.
    """
    return WaveContext.model_validate(data)


def load_wave_registry(raw_waves: Mapping[str, Mapping]) -> WaveRegistry:
    """
    Validate and load many waves at once.
    """
    validated = {
        wave_label: load_wave_context(payload)
        for wave_label, payload in raw_waves.items()
    }
    return WaveRegistry(waves=validated)


# ============================================================
# Useful comparison helpers
# ============================================================

def pct_point_change(old: int, new: int) -> int:
    return new - old


def compare_financial_deterioration(old_wave: WaveContext, new_wave: WaveContext) -> dict[str, int | str]:
    old_val = old_wave.finance.headline.financial_position_deteriorated_due_to_rising_costs_pct
    new_val = new_wave.finance.headline.financial_position_deteriorated_due_to_rising_costs_pct

    return {
        "metric": "financial_position_deteriorated_due_to_rising_costs_pct",
        "old_wave": old_wave.meta.wave_label,
        "new_wave": new_wave.meta.wave_label,
        "old_value": old_val,
        "new_value": new_val,
        "change_pct_points": pct_point_change(old_val, new_val),
    }


def compare_demand_increase(old_wave: WaveContext, new_wave: WaveContext) -> dict[str, int | str]:
    old_val = old_wave.demand.headline.increasing_demand_for_services_pct
    new_val = new_wave.demand.headline.increasing_demand_for_services_pct

    return {
        "metric": "increasing_demand_for_services_pct",
        "old_wave": old_wave.meta.wave_label,
        "new_wave": new_wave.meta.wave_label,
        "old_value": old_val,
        "new_value": new_val,
        "change_pct_points": pct_point_change(old_val, new_val),
    }


def compare_staff_recruitment(old_wave: WaveContext, new_wave: WaveContext) -> dict[str, int | str]:
    old_val = old_wave.workforce.recruitment_and_retention_concerns.staff_recruitment_concern_pct
    new_val = new_wave.workforce.recruitment_and_retention_concerns.staff_recruitment_concern_pct

    return {
        "metric": "staff_recruitment_concern_pct",
        "old_wave": old_wave.meta.wave_label,
        "new_wave": new_wave.meta.wave_label,
        "old_value": old_val,
        "new_value": new_val,
        "change_pct_points": pct_point_change(old_val, new_val),
    }


def _get_attr_path(obj: Any, path: str) -> Any:
    """
    Safely resolve a dotted attribute path like "demand.headline.increasing_demand_for_services_pct".

    Returns None if any intermediate attribute is missing.
    """
    current = obj
    for part in path.split("."):
        if not hasattr(current, part):
            return None
        current = getattr(current, part)
    return current


def trend_series(
    registry: WaveRegistry,
    attr_path: str,
) -> list[dict[str, Any]]:
    """
    Build a simple wave-numbered trend series for a given metric path.

    - attr_path is a dotted path from WaveContext root, e.g.:
      "demand.headline.increasing_demand_for_services_pct"
    - Skips waves where the value is missing (None or attribute absent).
    - Returns a list of dicts sorted by wave_number:
      [{"wave_label": str, "wave_number": int, "value": Any}, ...]
    """
    points: list[dict[str, Any]] = []

    for label in registry.list_waves():
        wave = registry.get(label)
        value = _get_attr_path(wave, attr_path)
        if value is None:
            continue
        points.append(
            {
                "wave_label": wave.meta.wave_label,
                "wave_number": wave.meta.wave_number,
                "value": value,
            }
        )

    return sorted(points, key=lambda row: row["wave_number"])


# ---------------------------------------------------------------------------
# Registry of key metrics for trend analysis
# ---------------------------------------------------------------------------

TREND_METRICS: list[dict[str, str]] = [
    {
        "id": "demand_increase",
        "label": "Demand increased",
        "section": "Demand & finance",
        "attr_path": "demand.headline.increasing_demand_for_services_pct",
    },
    {
        "id": "finance_deteriorated_costs",
        "label": "Finances deteriorated (rising costs)",
        "section": "Demand & finance",
        "attr_path": "finance.headline.financial_position_deteriorated_due_to_rising_costs_pct",
    },
    {
        "id": "operating_likely",
        "label": "Likely operating next year",
        "section": "Demand & finance",
        "attr_path": "operations.headline.likelihood_of_operating_this_time_next_year_pct",
    },
    {
        "id": "has_volunteers",
        "label": "Has volunteers",
        "section": "Workforce & volunteering",
        "attr_path": "workforce.headline.has_volunteers_pct",
    },
    {
        "id": "has_paid_staff",
        "label": "Has paid staff",
        "section": "Workforce & volunteering",
        "attr_path": "workforce.headline.has_paid_staff_pct",
    },
    {
        "id": "staff_rec_difficulty",
        "label": "Staff recruitment difficulties",
        "section": "Workforce & volunteering",
        "attr_path": "workforce.headline.face_staff_recruitment_difficulties_pct",
    },
    {
        "id": "staff_ret_difficulty",
        "label": "Staff retention difficulties",
        "section": "Workforce & volunteering",
        "attr_path": "workforce.headline.face_staff_retention_difficulties_pct",
    },
    {
        "id": "vol_rec_difficulty",
        "label": "Volunteer recruitment difficulties",
        "section": "Workforce & volunteering",
        "attr_path": "workforce.headline.face_volunteer_recruitment_difficulties_pct",
    },
    {
        "id": "vol_ret_difficulty",
        "label": "Volunteer retention difficulties",
        "section": "Workforce & volunteering",
        "attr_path": "workforce.headline.face_volunteer_retention_difficulties_pct",
    },
    {
        "id": "too_few_volunteers",
        "label": "Too few volunteers",
        "section": "Workforce & volunteering",
        "attr_path": "workforce.headline.too_few_volunteers_pct",
    },
    {
        "id": "has_reserves",
        "label": "Has financial reserves",
        "section": "Demand & finance",
        "attr_path": "headline_kpis.financial_health.has_financial_reserves_pct",
    },
    {
        "id": "using_reserves",
        "label": "Using reserves (of those with reserves)",
        "section": "Demand & finance",
        "attr_path": "headline_kpis.financial_health.using_reserves_among_those_with_reserves_pct",
    },
    {
        "id": "income_top_concern",
        "label": "Income as a top concern",
        "section": "Organisational concerns",
        "attr_path": "key_organisational_concerns.top_cards.income_pct",
    },
    {
        "id": "demand_top_concern",
        "label": "Increasing demand as a top concern",
        "section": "Organisational concerns",
        "attr_path": "key_organisational_concerns.top_cards.increasing_demand_for_services_pct",
    },
    {
        "id": "inflation_top_concern",
        "label": "Inflation (non-energy) as a top concern",
        "section": "Organisational concerns",
        "attr_path": "key_organisational_concerns.top_cards.inflation_goods_and_services_prices_other_than_energy_pct",
    },
]


# ============================================================
# Example Wave 1 raw payload
# ============================================================

WAVE1_RAW = {
    "meta": {
        "title": "Key Performance Indicators",
        "subtitle": "Unlock Insights from the Welsh Voluntary Sector",
        "wave_label": "Wave 1",
        "wave_number": 1,
        "wave_response_count": 99,
        "wave_response_desc": "99 organisations responded to Wave 1",
    },
    "headline_kpis": {
        "financial_health": {
            "financial_position_deteriorated_due_to_rising_costs_pct": 74,
            "using_reserves_to_cover_operational_costs_pct": 48,
        },
        "workforce": {
            "has_volunteers_pct": 93,
            "has_paid_staff_pct": 93,
            "face_staff_recruitment_difficulties_pct": 27,
            "face_staff_retention_difficulties_pct": 23,
            "face_volunteer_recruitment_difficulties_pct": 35,
            "face_volunteer_retention_difficulties_pct": 31,
        },
        "operations": {
            "likelihood_of_operating_this_time_next_year_pct": 77,
            "report_insufficient_capacity_to_meet_demand_next_3_months_pct": 65,
        },
    },
    "key_organisational_concerns": {
        "section_title": "Operational Challenges",
        "organisations_answered": 96,
        "top_cards": {
            "income_pct": 90,
            "increasing_demand_for_services_pct": 56,
            "inflation_goods_and_services_prices_other_than_energy_pct": 38,
        },
        "ranked_concerns": [
            {"rank": 1, "concern": "Income", "pct": 90},
            {"rank": 2, "concern": "Increasing demand for services", "pct": 56},
            {"rank": 3, "concern": "Inflation of goods and services prices (other than energy)", "pct": 38},
            {"rank": 4, "concern": "Recruitment of volunteers", "pct": 30},
            {"rank": 5, "concern": "Other (please specify)", "pct": 23},
            {"rank": 6, "concern": "Retention of paid staff", "pct": 23},
            {"rank": 7, "concern": "Recruitment of paid staff", "pct": 14},
            {"rank": 8, "concern": "Energy prices", "pct": 10},
            {"rank": 9, "concern": "Retention of volunteers", "pct": 10},
            {"rank": 10, "concern": "Changes to interest rates", "pct": 3},
            {"rank": 11, "concern": "Decreasing demand for services", "pct": 3},
        ],
    },
    "finance": {
        "headline": {
            "using_reserves_to_cover_operational_costs_pct": 48,
            "no_reserves_available_pct": 12,
            "financial_position_deteriorated_due_to_rising_costs_pct": 74,
            # removed: "has_financial_reserves_pct": 88,
            # removed: "using_reserves_among_those_with_reserves_pct": 48,
        },
        "income_breakdown": {
            "section_title": "Breakdown of Income by Funding Source",
            "organisations_answered": 99,
            "sources_pct": {
                "local_authority_or_health_board_grants": 11,
                "grants_from_uk_government": 5,
                "grants_from_welsh_government": 18,
                "contracts_for_service_delivery": 13,
                "grants_from_trusts_and_or_foundations": 24,
                "trading_income": 10,
                "donations_from_the_public_including_regular_giving": 10,
                "legacy_giving_wills": 1,
                "corporate_support_or_sponsorship": 2,
                "events_fundraising_including_volunteer_led_events_and_challenge_events": 4,
                "major_donor": 0,
                "payroll_giving": 0,
                "raffles_and_lotteries": 1,
                "investment_income": 1,
            },
        },
        "expenditure_breakdown": {
            "section_title": "Breakdown of Expenditure by Cost Category",
            "organisations_answered": 99,
            "categories_pct": {
                "energy": 3,
                "staffing": 56,
                "property_premises": 8,
                "goods_materials": 8,
                "services": 14,
                "other": 11,
            },
        },
        "change_past_3_months": {
            "section_title": "Change in financial position past 3 months",
            "improved_a_lot_pct": 5,
            "improved_a_little_pct": 19,
            "stayed_the_same_pct": 41,
            "deteriorated_a_little_pct": 31,
            "deteriorated_a_lot_pct": 4,
        },
        "expected_change_next_3_months": {
            "section_title": "Expected Change in Financial Position Over the Next 3 Months",
            "deteriorate_a_lot_pct": 7,
            "deteriorate_a_little_pct": 20,
            "stay_the_same_pct": 44,
            "improve_a_little_pct": 24,
            "improve_a_lot_pct": 5,
        },
        "actions_taken_due_to_rising_costs": {
            "section_title": "Actions Taken due to Rising Costs",
            "organisations_answered": 77,
            "actions_pct": {
                "previously_unplanned_use_of_reserves": 38,
                "had_to_increase_price_of_services": 35,
                "renegotiated_grants_commissioned_contracts": 34,
                "reduced_level_or_number_of_services": 31,
                "had_to_make_redundancies_or_release_staff": 30,
                "had_to_increase_volunteer_responsibilities_and_or_hours": 21,
                "had_to_reduce_staff_hours": 18,
                "had_to_reduce_office_workspace": 13,
                "other": 12,
                "taken_on_debt": 4,
                "sold_assets": 3,
                "cancelled_existing_grants_commissioned_contracts": 1,
            },
        },
    },
    "demand": {
        "headline": {
            "increasing_demand_for_services_pct": 56,
            "report_insufficient_capacity_to_meet_demand_next_3_months_pct": 65,
        },
        "change_past_3_months": {
            "section_title": "Change in Service Demand Past 3 Months",
            "increased_a_lot_pct": 31,
            "increased_a_little_pct": 33,
            "stayed_the_same_pct": 34,
            "decreased_a_little_pct": 2,
            "decreased_a_lot_pct": 0,
        },
        "expected_change_next_3_months": {
            "section_title": "Expected Change in Service Demand Over the Next 3 Months",
            "decrease_a_lot_pct": 0,
            "decrease_a_little_pct": 2,
            "stay_the_same_pct": 28,
            "increase_a_little_pct": 37,
            "increase_a_lot_pct": 31,
        },
        "ability_to_meet_demand_next_3_months": {
            "section_title": "Ability to meet demand over the next 3 months",
            "we_expect_to_meet_demand_with_limited_no_spare_capacity_pct": 65,
            "we_expect_to_almost_meet_demand_pct": 26,
            "we_expect_to_fall_significantly_short_in_our_ability_to_meet_demand_pct": 6,
            "we_expect_to_meet_demand_with_significant_spare_capacity_pct": 3,
        },
    },
    "workforce": {
        "headline": {
            "has_volunteers_pct": 93,
            "has_paid_staff_pct": 93,
            "face_staff_recruitment_difficulties_pct": 27,
            "face_staff_retention_difficulties_pct": 23,
            "face_volunteer_recruitment_difficulties_pct": 35,
            "face_volunteer_retention_difficulties_pct": 31,
        },
        "recruitment_and_retention_concerns": {
            "staff_recruitment_concern_pct": 27,
            "staff_retention_concern_pct": 23,
            "volunteer_recruitment_concern_pct": 35,
            "volunteer_retention_concern_pct": 31,
        },
        "impact_of_recruitment_difficulties": {
            "section_title": "Impact of Recruitment Difficulties",
            "employees_working_increased_hours_pct": 60,
            "volunteers_working_increased_hours_pct": 40,
            "had_to_pause_some_operations_pct": 38,
            "unable_to_meet_demand_pct": 36,
            "had_to_recruit_temporary_workers_pct": 14,
            "other_pct": 12,
        },
        "change_in_paid_staff_numbers_last_3_months": {
            "section_title": "Change in Paid Staff Numbers, Last 3 Months",
            "decreased_a_lot_pct": 2,
            "decreased_a_little_pct": 13,
            "stayed_the_same_pct": 67,
            "increased_a_little_pct": 17,
            "increased_a_lot_pct": 1,
        },
        "change_in_volunteer_numbers_last_3_months": {
            "section_title": "Change in Volunteer Numbers, Last 3 Months",
            "decreased_a_lot_pct": 1,
            "decreased_a_little_pct": 7,
            "stayed_the_same_pct": 56,
            "increased_a_little_pct": 32,
            "increased_a_lot_pct": 3,
        },
        "expected_change_in_paid_staff_numbers_next_3_months": {
            "section_title": "Expected Change in Paid Staff Numbers Over the Next 3 Months",
            "decrease_a_lot_pct": 1,
            "decrease_a_little_pct": 13,
            "stay_the_same_pct": 68,
            "increase_a_little_pct": 13,
            "increase_a_lot_pct": 3,
        },
        "expected_change_in_volunteer_numbers_next_3_months": {
            "section_title": "Expected Change in Volunteer Numbers Over the Next 3 Months",
            "decrease_a_lot_pct": 0,
            "decrease_a_little_pct": 5,
            "stay_the_same_pct": 52,
            "increase_a_little_pct": 38,
            "increase_a_lot_pct": 4,
        },
    },
    "operations": {
        "headline": {
            "likelihood_of_operating_this_time_next_year_pct": 77,
            "report_insufficient_capacity_to_meet_demand_next_3_months_pct": 65,
        },
    },
    "respondent_profile": {
        "section_title": "Respondent Profile",
        "subtitle": "Overview of Participating Organisations (Size, Activity, Location, Employment)",
        "responses_by_survey_wave": 99,
        "main_activities_of_participating_organisations": {
            "other_charitable_purposes": 20,
            "prevention_or_relief_of_poverty": 12,
            "disability_support": 12,
            "health_and_saving_lives": 10,
            "education_and_research": 9,
            "arts_culture_and_heritage": 8,
            "economic_and_community_development": 7,
            "human_rights_and_equality": 6,
            "recreation_and_community_spaces": 6,
            "environment_and_conservation": 6,
            "religion": 1,
            "animal_protection": 1,
            "accommodation_and_housing": 1,
        },
        "organisation_size_by_income_band": {
            "small_pct": 22,
            "medium_pct": 40,
            "large_pct": 37,
        },
        "number_of_paid_staff_employed_by_organisations": {
            "1_to_10_pct": 50,
            "11_to_50_pct": 30,
            "51_to_250_pct": 17,
            "250_plus_pct": 3,
        },
    },
}


# ============================================================
# Example usage
# ============================================================

WAVE1_CONTEXT = load_wave_context(WAVE1_RAW)

ALL_WAVES_RAW = {
    "Wave 1": WAVE1_RAW,
    # "Wave 2": WAVE2_RAW,
    # "Wave 3": WAVE3_RAW,
}

WAVE_REGISTRY = load_wave_registry(ALL_WAVES_RAW)

# Access
# WAVE_REGISTRY.get("Wave 1").finance.headline.financial_position_deteriorated_due_to_rising_costs_pct

# Comparison, once Wave 2 exists
# result = compare_financial_deterioration(
#     WAVE_REGISTRY.get("Wave 1"),
#     WAVE_REGISTRY.get("Wave 2"),
# )
# print(result)
