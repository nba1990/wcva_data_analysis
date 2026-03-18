# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
Quick comparison of key metrics between:
- EDA aggregates (eda.py)
- WaveContext instances (wave_context.py)

Run with:

    python -m src.debug_metrics
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.data_loader import load_dataset
from src.eda import volunteer_recruitment_analysis, workforce_operations
from src.wave_context import build_wave_context_from_df


def main() -> None:
    df = load_dataset()
    rec = volunteer_recruitment_analysis(df)
    wf = workforce_operations(df)

    wave2_ctx = build_wave_context_from_df(df, wave_label="Wave 2", wave_number=2)

    rows: list[dict[str, Any]] = [
        {
            "metric": "Too few volunteers %",
            "source": "EDA (pct_too_few)",
            "value": rec["pct_too_few"],
        },
        {
            "metric": "Too few volunteers %",
            "source": "WaveContext (workforce.headline.too_few_volunteers_pct)",
            "value": wave2_ctx.workforce.headline.too_few_volunteers_pct,
        },
        {
            "metric": "Has reserves %",
            "source": "EDA (reserves_yes_pct)",
            "value": wf["reserves_yes_pct"],
        },
        {
            "metric": "Has reserves %",
            "source": "WaveContext (headline_kpis.financial_health.has_financial_reserves_pct)",
            "value": wave2_ctx.headline_kpis.financial_health.has_financial_reserves_pct,
        },
        {
            "metric": "Using reserves (of those with reserves) %",
            "source": "EDA (using_reserves_pct)",
            "value": wf["using_reserves_pct"],
        },
        {
            "metric": "Using reserves (of those with reserves) %",
            "source": "WaveContext (headline_kpis.financial_health.using_reserves_among_those_with_reserves_pct)",
            "value": wave2_ctx.headline_kpis.financial_health.using_reserves_among_those_with_reserves_pct,
        },
    ]

    df_comp = pd.DataFrame(rows)

    # Add a simple "match" flag for consecutive EDA/WaveContext rows of the same metric
    tolerance = 0.5  # allowed absolute difference
    df_comp["match"] = ""
    for metric in df_comp["metric"].unique():
        subset = df_comp[df_comp["metric"] == metric]
        if len(subset) == 2:
            v1, v2 = subset["value"].iloc[0], subset["value"].iloc[1]
            ok = abs(float(v1) - float(v2)) <= tolerance
            df_comp.loc[subset.index, "match"] = ok

    print(df_comp.to_string(index=False))


if __name__ == "__main__":
    main()
# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
