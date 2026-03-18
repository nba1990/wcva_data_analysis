from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from src.config import StreamlitAppUISharedConfigState


@dataclass(frozen=True)
class PageContext:
    """
    Shared context passed to each section page render function.

    Attributes:
        df: Filtered analysis DataFrame for the current view.
        df_full: Full underlying dataset before filters (for pages that need it).
        n: Number of organisations in the filtered view.
        ui_config: Per-session UI configuration (filters, suppression, palette).
        prof: High-level profile summary for the current view
            (from profile_summary()).
        asset_report: Output from check_runtime_assets() for deployment health.
    """

    df: pd.DataFrame
    df_full: pd.DataFrame
    n: int
    ui_config: StreamlitAppUISharedConfigState
    prof: Dict[str, Any]
    asset_report: Dict[str, Any]
