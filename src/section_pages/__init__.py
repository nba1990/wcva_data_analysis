# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
Section page modules for the Baromedr Cymru Wave 2 dashboard.

Each module exposes a single `render_page(context: PageContext)` entrypoint
plus one or more internal `render_*` helpers. The shared `PageContext`
dataclass (defined in ``src.page_context``) carries the filtered DataFrame,
full dataset, per-session UI config, and any precomputed aggregates.

Page dispatch and construction of `PageContext` live in ``src.app``; navigation
IDs in ``src.navigation.NAV_ITEMS`` must match the keys used in
``PAGE_RENDERERS`` in ``src.app``.

Modules: at_a_glance, concerns_and_risks, data_notes, demographics_and_types,
deployment_health, earned_settlement, executive_summary, overview,
sroi_references, trends_and_waves, volunteer_recruitment, volunteer_retention,
workforce_and_operations.
"""

# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
