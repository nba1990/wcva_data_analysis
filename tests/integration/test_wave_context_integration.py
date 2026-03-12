from __future__ import annotations

from src.data_loader import _derive_columns
from src.eda import (
    demand_and_outlook,
    volunteer_recruitment_analysis,
    workforce_operations,
)
from src.wave_context import build_wave_context_from_df


def test_wave_context_headlines_align_with_eda(tiny_df) -> None:
    """
    Service-level integration: WaveContext built from a DataFrame should
    reproduce the same headline percentages as the EDA helpers.
    """
    derived = _derive_columns(tiny_df.copy())
    dem = demand_and_outlook(derived)
    wf = workforce_operations(derived)
    rec = volunteer_recruitment_analysis(derived)

    ctx = build_wave_context_from_df(derived, wave_label="Wave X", wave_number=2)

    assert ctx.demand.headline.increasing_demand_for_services_pct == int(
        round(dem["demand_pct_increased"])
    )
    assert (
        ctx.finance.headline.financial_position_deteriorated_due_to_rising_costs_pct
        == int(round(wf["finance_deteriorated_pct"]))
    )
    assert ctx.workforce.headline.too_few_volunteers_pct == int(
        round(rec["pct_too_few"])
    )
