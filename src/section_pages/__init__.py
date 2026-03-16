# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""
Section page modules for the Baromedr Cymru Wave 2 dashboard.

Each module exposes a `render_*` function that takes the filtered DataFrame
and any required context (e.g. n, suppressed), and writes directly to Streamlit
(st.title, st.markdown, charts via show_chart, etc.). Page dispatch is in
src/app.py; navigation IDs in src/navigation.NAV_ITEMS must match.

Modules: at_a_glance, concerns_and_risks, data_notes, demographics_and_types,
deployment_health, earned_settlement, executive_summary, overview,
sroi_references, trends_and_waves, volunteer_recruitment, volunteer_retention,
workforce_and_operations.
"""

# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
