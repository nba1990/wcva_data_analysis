Architecture overview
=====================

This page summarises how the dashboard is structured. For the full document, see the repository file ``ARCHITECTURE.md``.

High-level flow
---------------

::

   Browser ⇄ Streamlit frontend ⇄ src/app.py
       → Data layer: data_loader.py, eda.py, wave_context.py
       → Visualisation: charts.py, sroi_charts/sroi_figures.py
       → Section pages: src/section_pages/*
       → References: references/SROI_Wales_Voluntary_Sector/*

Entry point — ``src/app.py``
----------------------------

* Sets Streamlit page config (title, layout).
* Runs a runtime asset check before loading data; if required files are missing the app shows a health view and stops early.
* Loads the dataset via ``data_loader.load_dataset()`` with ``st.cache_data``.
* Sidebar: accessibility controls and filters (org size, scope, LA, activity, paid staff, concerns), backed by per-session UI config from ``get_app_ui_config()`` (stored in ``st.session_state["app_ui_config"]``).
* Renders sidebar navigation (``navigation.render_sidebar_nav``) and dispatches to the appropriate ``render_*`` in ``src/section_pages``.

Navigation — ``src/navigation.py``
-----------------------------------

* ``NavItem`` dataclass and ``NAV_ITEMS`` list (id, label, subtitle, icon).
* ``get_default_page()``, ``get_nav_item_ids()``, ``render_sidebar_nav()``.
* Nav IDs must match the page dispatch keys in ``app.py``.

Section pages — ``src/section_pages/*``
---------------------------------------

Each file defines a ``render_*`` function that:

* Takes the filtered DataFrame (and often ``n`` and/or ``suppressed``).
* Calls analytical helpers from ``eda.py`` and ``wave_context.py``.
* Uses chart helpers from ``charts.py`` and ``sroi_charts/sroi_figures.py``.
* Respects accessibility config (e.g. ``mode``, ``show_chart`` which applies ``get_app_ui_config().text_scale``).

Data and analysis
-----------------

* **data_loader.py**: Loads CSV, cleans, adds derived columns (region, demand_direction, finance_deteriorated, multi-select counts). ``load_la_context()`` is cached, and ``check_runtime_assets()`` verifies deployment files.
* **eda.py**: Reusable analysis (profile_summary, demand_and_outlook, workforce_operations, volunteer_recruitment_analysis, volunteer_retention_analysis, executive_highlights, etc.). Percentages use non-missing bases per question.
* **wave_context.py**: Pydantic models for wave-level context; build_wave_context_from_df, get_wave_registry, comparison and trend helpers.

Charts and UI
-------------

* **charts.py**: WCVA-branded Plotly helpers (horizontal_bar_ranked, stacked_bar_ordinal, donut_chart, grouped_bar, heatmap_matrix, wave_trend_line, kpi_card_html). ``show_chart()`` displays with optional text scaling and CSV download.
* **config.py**: Palettes, response orderings, K_ANON_THRESHOLD, StreamlitAppUISharedConfigState, AltTextConfig, label groupers.
* **sroi_charts/sroi_figures.py**: SROI evidence chart factories (funding flows, SROI comparison, volunteering value, etc.).
* **deployment_health.py**: Operational page for required/optional runtime asset status and deployment diagnostics.

Multi-user behaviour
--------------------

* Each browser session has its own ``st.session_state``; UI config is per-session via ``get_app_ui_config()``.
* The main dataset is loaded once with ``st.cache_data`` and shared read-only across sessions.
* Results are suppressed when the filtered sample size is below ``K_ANON_THRESHOLD`` (default 5).

Further reading
---------------

* **ARCHITECTURE.md** (in repo): Full architecture, deployment, and “where to look when extending”.
* **docs/adr/**: Architecture Decision Records (Streamlit UI, navigation, SROI charts, state/caching, Docker, CI and testing).
* **docs/LEARNING_AND_BACKLOG.md**: Backlog, testing strategy, coverage goals, fixture notes.
