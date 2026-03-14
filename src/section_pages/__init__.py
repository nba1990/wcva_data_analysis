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
