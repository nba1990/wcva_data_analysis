<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# WCVA Baromedr Wave 2 – Architecture Overview

This document explains how the dashboard is structured, how the main modules interact, and what to keep in mind when extending it. It assumes general Python knowledge but no prior Streamlit experience.

**Code documentation**: Modules, classes, and public functions are documented with docstrings (summary, Args, Returns where useful). Type hints are used on function parameters and return values. See `CONTRIBUTING.md` §7 for the project’s documentation and typing standards. Build Sphinx docs with ``pip install -r docs/requirements-docs.txt`` then ``cd docs && make html`` (output in ``docs/build/html/``).

## 1. High‑level architecture

Text diagram of the main flow:

Browser ⇄ Streamlit frontend ⇄ `src/app.py` (backend script)
→ Data layer: `data_loader.py`, `eda.py`, `wave_context.py`
→ Visualisation layer: `charts.py`, `sroi_charts/sroi_figures.py`
→ Section pages: `src/section_pages/*`
→ References and offline artefacts: `references/SROI_Wales_Voluntary_Sector/*`

### 1.1 Entry point – `src/app.py`

- Configures the Streamlit page (title, layout, favicon).
- Resolves the runtime dataset source before loading data and falls back to the bundled sample fixture in explicit demo mode when the private Wave dataset is unavailable.
- Loads the Wave 2 dataset via `data_loader.load_dataset()` using `st.cache_data` so all users share the same read‑only DataFrame and the resolved runtime-source metadata.
- Sets up the sidebar:
  - Accessibility controls (text size, colour‑blind friendly palette) backed by per-session UI config from `get_app_ui_config()` (stored in `st.session_state["app_ui_config"]`).
  - Filter controls (organisation size, scope, local authority, main activity, paid staff, selected concerns).
  - Computes a filtered `df` and the filtered base size `n`.
  - Derives a suppression flag when `n < K_ANON_THRESHOLD` and exposes it via the shared config state.
- Renders the WCVA‑branded sidebar navigation using `navigation.render_sidebar_nav` and dispatches to the appropriate `render_*` function from `src/section_pages`.

### 1.2 Navigation – `src/navigation.py`

- Defines a `NavItem` dataclass and a `NAV_ITEMS` list describing the sidebar sections (id, label, subtitle, icon).
- Exposes helpers:
  - `get_default_page()` – which page to open first.
  - `get_nav_item_ids()` – ordered list of page ids.
  - `render_sidebar_nav()` – renders the pill‑style sidebar, tracks `st.session_state["current_page"]`, and reruns the app when the user switches page.
- The tests in `tests/unit/test_navigation.py` ensure:
  - `NAV_ITEMS` ids are unique.
  - Every id is wired into the `if/elif` dispatch block in `app.py`.
  - The `Deployment Health` page remains present in navigation.

### 1.3 Section pages – `src/section_pages/*`

Each file in `src/section_pages/` defines a `render_*` function responsible for a single dashboard page. They:

- Take the filtered DataFrame (and often `n` and/or `suppressed`) as arguments.
- Call analytical helpers from `src/eda.py` and `src/wave_context.py`.
- Use chart helpers from `src/charts.py` for generic visuals and from `src/sroi_charts/sroi_figures.py` for SROI‑specific visuals.
- Respect the shared accessibility configuration via:
  - The `mode` / `palette_mode` parameter on chart helpers.
  - The `show_chart` wrapper which applies `get_app_ui_config().text_scale`.

The `sroi_references.py` page is slightly different in that it:

- Weaves narrative text and references from the SROI briefing.
- Calls the SROI chart factories in `src/sroi_charts/sroi_figures.py`.
- Embeds a Markmap‑generated HTML mind‑map by reading the exported HTML file and passing it to `st.components.v1.html`.

The `deployment_health.py` page is operational rather than analytical:

- It renders the output of `data_loader.check_runtime_assets()`.
- It shows which runtime sources were resolved, whether the app is in real-data or demo mode, and which optional files are unavailable.
- It serves as the canonical in-app explanation of deployment state and runtime configuration.

## 2. Data and analytical layer

### 2.1 `src/data_loader.py`

- Responsible for loading the anonymised Wave 2 CSV from a runtime path, URL, local fallback, or bundled sample fixture.
- Applies light cleaning, derived columns, and joins against auxiliary context tables where needed.
- Exposes `check_runtime_assets()` to verify required and optional files for deployment, plus resolved runtime-source metadata.
- Returns a single canonical DataFrame that the rest of the app uses.

### 2.2 `src/eda.py`

- Houses reusable analytical helpers for the main dashboard stories, such as:
  - `demand_and_outlook(df)` – demand vs finance vs operating outlook.
  - `workforce_operations(df)` – workforce and reserves metrics.
  - `volunteer_recruitment_analysis(df)` / `volunteer_retention_analysis(df)`.
  - `profile_summary(df)` – profile of organisations in view (size, activity, geography).
- These helpers are used by:
  - `render_overview`, `render_executive_summary`, and other section pages.
  - Tests in `tests/test_wcva_metrics_wave2.py` and `tests/unit/test_metrics_executive_overview.py` (fixture‑based regression guards).

### 2.3 `src/wave_context.py` and per-wave schemas

- Encapsulates cross‑wave comparisons using a registry model.
- Provides helpers such as:
  - `get_wave_registry(df)` and `build_trend_long(...)` / `build_trend_pivot(...)`.
  - Comparison functions like `compare_demand_increase(...)` and `compare_financial_deterioration(...)`.
- Uses a small per‑wave schema and mapping layer:
  - `config/waves/wave2.schema.yml` (and future `waveN.schema.yml` files) describe how raw columns map onto a stable set of canonical metrics (e.g. demand increase, finances deteriorated, has volunteers, has reserves).
  - `src/wave_schema.py` loads these schemas and evaluates metrics via a tiny vocabulary (e.g. `share_eq`, `share_in`, `share_gt`, `conditional_share`), so cross‑wave trends are configured declaratively rather than hard‑coded per wave.
- Consumed by:
  - `render_trends_and_waves` for the cross‑wave trend table and charts.
  - `render_executive_summary` for contextual call‑outs and earliest vs latest comparisons.

## 3. Visualisation layer

### 3.1 Generic WCVA charts – `src/charts.py`

- Provides WCVA‑branded Plotly helpers:
  - `horizontal_bar_ranked`, `stacked_bar_ordinal`, `donut_chart`, `grouped_bar`, `heatmap_matrix`, and `kpi_card_html`.
  - `wave_trend_line` for consistent multi‑wave line charts.
  - `show_chart` for rendering figures in Streamlit with:
    - Dynamic text scaling driven by `get_app_ui_config().text_scale`.
    - Accessibility captions based on `_alt_text` attached to figures.
    - Optional data table and CSV download.
- All helpers take a `mode` parameter (`"brand"` or `"accessible"`) and use `get_palette` / `get_likert_colours` and other config from `src/config.py`.
- Unit tests in `tests/unit/test_charts_core.py` and `tests/unit/test_sroi_figures.py` assert that:
  - Figures are created as expected.
  - Alt‑text is set.
  - Colour modes and text scaling behave sensibly.

### 3.2 SROI‑specific charts – `src/sroi_charts/sroi_figures.py`

- Contains pure Plotly factories for SROI / evidence charts:
  - Funding flows, SROI comparison, volunteering value, measurement gap.
  - WCVA–WG funding, NLCF Wales.
  - Alignment heatmap between framework enablers and objectives.
  - The New Approach framework flow diagram (Plotly implementation).
  - Implementation timeline.
- Each `make_*` function accepts:
  - `palette_mode` (`"brand"` / `"accessible"`), used to derive colours from `ACCESSIBLE_SEQUENCE` and `BRAND_SEQUENCE`.
  - `text_scale`, passed into a shared `_scale_layout` helper which adjusts base and title font sizes.
- Used in two places:
  - The SROI Streamlit page (`src/section_pages/sroi_references.py`).
  - The offline batch generator script (`references/SROI_Wales_Voluntary_Sector/scripts/sroi_wales_voluntary_sector.py`) via `save_plotly_figure`.
- `tests/unit/test_sroi_figures.py` verifies:
  - Each factory returns a `go.Figure` with a non‑empty title.
  - Changing `palette_mode` alters bar / line colours.
  - Increasing `text_scale` results in larger font sizes in `layout`.

## 4. SROI references and offline artefacts

- Located under `references/SROI_Wales_Voluntary_Sector/`.
- The key script `scripts/sroi_wales_voluntary_sector.py`:
  - Calls the `make_*` SROI factories to generate a suite of PNG/SVG outputs plus JSON sidecar metadata.
  - Uses a dedicated Plotly implementation for the framework flow SVG to avoid Mermaid SVG rendering issues.
  - Writes artefacts into `references/SROI_Wales_Voluntary_Sector/output/`.
- Documents under `references/SROI_Wales_Voluntary_Sector/docs/` include:
  - The main SROI briefing in Markdown/PDF.
  - Markmap/Freeplane exports, including the `WCVA_Text_Interactive_MindMap.html` file embedded in the SROI Streamlit page.

## 5. Multi‑user and session model

Streamlit runs the same Python script per browser session, rerunning top‑to‑bottom on each interaction. Key points:

- **Per‑user state**:
  - User‑specific UI state (filters, accessibility choices, current page) is stored in `st.session_state`:
    - `st.session_state["current_page"]` for the active page id.
    - `st.session_state["app_ui_config"]` for the UI config dataclass (`StreamlitAppUISharedConfigState`), accessed via `get_app_ui_config()` from `src.config`. One instance per session; do not use a module-level singleton.
  - Each browser tab has its own session, so these values are isolated per user/tab.
- **Shared resources**:
  - The dataset is loaded once per process using `@st.cache_data` (`get_data()` in `app.py`), so all users share a single in‑memory copy and the same resolved runtime-source metadata.
  - The local-authority context CSV is loaded via `load_la_context()` in `data_loader.py`, which is cached with `@functools.lru_cache` so it is read from disk once per process.
  - The SROI mind-map HTML is loaded via `_get_mindmap_html()` in `sroi_references.py`, cached with `@st.cache_data`.
  - Heavy or external resources (if any) should use `st.cache_resource`.
- **Performance**:
  - Filtering starts from `df_full` without an extra `.copy()`; each filter step produces a new DataFrame.
  - Optional debug flag `DEBUG_MEMORY` (env `WCVA_DEBUG_MEMORY`) enables process memory display in the sidebar for tuning.
  - `app.py` reads the debug flag directly from the environment, which avoids a brittle import dependency during deployment startup.
- **Safe vs unsafe patterns**:
  - Safe:
    - Use `st.session_state` or small, immutable dataclasses for user preferences.
    - Use `st.cache_data` for read‑only, deterministic data loading.
  - Unsafe:
    - Mutable module‑level globals that are updated per request (can leak state between users).
    - Keeping open connections or cursors in globals without a clear lifecycle.
  - The current design keeps user‑specific data in session state and uses globals only for configuration constants and palette definitions.

## 6. How a typical request flows

1. User interacts with the sidebar (changes a filter or clicks a different page button).
2. Streamlit reruns `src/app.py` from the top for that session.
3. `get_data()` returns the cached full dataset.
4. Sidebar widgets read and update the per-session UI config (from `get_app_ui_config()`) with current filters and accessibility preferences.
5. Filtering logic applies the selected filters to `df_full` to produce `df` and counts `n`.
6. Suppression logic sets `get_app_ui_config().suppressed` if `n < K_ANON_THRESHOLD`.
7. Navigation determines `page`, and the corresponding `render_*` function is called with `df`, `n`, and `suppressed` as appropriate.
8. The page:
   - Calls EDA helpers to compute aggregates.
   - Builds charts via `charts` / `sroi_charts`.
   - Renders them using `show_chart` / `st.plotly_chart` with accessibility options applied.

## 7. SROI & References page specifics

The SROI & References page (`src/section_pages/sroi_references.py`) brings several strands together:

- Reads the per-session accessibility configuration via `get_app_ui_config()`:
  - `palette_mode = get_app_ui_config().palette_mode`
  - `text_scale = get_app_ui_config().text_scale or 1.0`
- Creates interactive Plotly charts using the SROI factories, passing `palette_mode` and `text_scale` into each.
- Embeds the interactive Markmap HTML mind‑map:
  - Loads the HTML via `_get_mindmap_html()` (cached with `@st.cache_data`).
  - Injects it into the page with `st.components.v1.html(html, height=1920, scrolling=True)`.
- Provides textual summaries, references, and caveats about SROI methodology and the formal vs informal volunteering measurement gap.

## 8. Where to look when extending the app

- **New pages**:
  - Add a `render_*` function to `src/section_pages/`.
  - Add a matching `NavItem` in `src/navigation.py`.
  - Wire the new page id into the `if/elif` dispatch block in `src/app.py`.
- **New charts**:
  - Prefer adding reusable helpers to `src/charts.py` or `src/sroi_charts/sroi_figures.py` rather than writing Plotly code inline.
  - Use `mode` / `palette_mode` and `text_scale` consistently.
  - Attach `_alt_text` where helpful for accessibility and rely on `show_chart` to surface it.
- **New data logic**:
  - Add or extend helpers in `src/eda.py` and, for cross‑wave stories, in `src/wave_context.py`.
  - Add regression tests in `tests/unit` and/or `tests/integration` to pin down key numbers.

### 8.1 Deployment and Docker

The app can be run in a container for self-hosting or deployment. A `Dockerfile` and `docker-compose.yml` are provided; full instructions (build, run, runtime data configuration, reverse proxy, env vars) are in **`docs/DOCKER_AND_DEPLOYMENT.md`**. Streamlit Community Cloud remains an option without Docker (see README).

The runtime-data model in `src/app.py` adds one extra protection for hosted environments: if the private dataset is unavailable, the app falls back to the bundled sample fixture and marks the session as demo mode instead of failing deeper in the analysis code.

---

## 9. Developer tour: tests and docs

A short “tour” for maintainers and new developers: where to look first and how the tests and docs fit together.

### 9.1 Tests – what they guard

- **`tests/unit/test_navigation.py`**
  Ensures every sidebar page is wired: `NAV_ITEMS` IDs are unique and each ID is handled in the `app.py` dispatch block. Add a new page → add a `NavItem` and an `elif page == "new_id"` (or equivalent) and the test continues to pass.

- **`tests/unit/test_sroi_figures.py`**
  Covers all SROI chart factories: each returns a `go.Figure` with a non‑empty title, and `palette_mode` / `text_scale` change colours and font sizes. Uses `fig.to_dict()` to read layout and trace data (including `colorscale` for heatmaps).

- **`tests/unit/test_metrics_executive_overview.py`**
  Regression guard for Overview/Executive metrics. Loads `tests/fixtures/wcva_sample_dataset.csv` via `load_dataset()` (so derived columns exist), then runs `demand_and_outlook`, `workforce_operations`, and `profile_summary` and asserts fixed percentages (e.g. demand increased, financial deteriorated, has_volunteers_pct). If you change EDA logic or the fixture, update the expected values or the fixture so the test still reflects the intended behaviour.

- **`tests/fixtures/wcva_sample_dataset.csv`**
  Small CSV with **raw** questionnaire columns (`demand`, `financial`, `shortage_staff_rec`, etc.) so that `load_dataset()` can run `_clean` and `_derive_columns` and produce the same derived columns the app uses. Keep this in sync with `data_loader` and `eda` column expectations.

### 9.2 Docs – where to read

- **`README.md`** – Quickstart, structure, testing, deployment (including Docker), SROI page, multi‑user behaviour. Also has a **"New here? Picking this up again?"** orientation and a **Documentation index** table of all key docs.
- **`ARCHITECTURE.md`** (this file) – Flow, modules, session model, performance/caching, how to extend, developer tour, future dashboards.
- **`docs/adr/`** – ADR-001 (Streamlit), ADR-002 (navigation), ADR-003 (SROI charts), ADR-004 (state and caching), ADR-005 (Docker and self-hosting), ADR-006 (CI and testing), ADR-007 (runtime data and demo mode). Read these when changing UI framework, nav, SROI chart location, session/cache design, deployment approach, CI/test pipeline, or runtime data behaviour.
- **`docs/DOCKER_AND_DEPLOYMENT.md`** – Docker build/run, docker-compose, self-hosting, and deployment options.
- **`docs/LEARNING_AND_BACKLOG.md`** – Backlog items (PyGWalker, DuckDB, PyDeck, new dashboards), testing strategy notes, and pointers to policy questions and plans.
- **`docs/learning/`** – Curated learning guides that explain how this repo handles private data, deployment, testing, releases, and git hygiene for a Python/data-science audience.

---

## 10. Future dashboards and backlog

The following are **not** part of the current WCVA Baromedr dashboard but are useful as a backlog and for learning from past plans:

- **Retrofit Impact Dashboard** – Separate app or page for retrofit/energy efficiency impact (if data becomes available).
- **Fuel Poverty Risk Map** – Geospatial view (e.g. PyDeck) of fuel poverty risk by area, overlaying voluntary sector presence if data allows.
- **Community Energy Investment Simulator** – Exploratory idea from prior discussions; no current implementation.

When adding a **new evidence‑style or narrative page** (like the SROI page), reuse the same pattern:

1. Add `render_*` in `src/section_pages/`, a `NavItem` in `src/navigation.py`, and dispatch in `app.py`.
2. Prefer shared chart helpers in `src/charts.py` or `src/sroi_charts/sroi_figures.py` with `palette_mode` and `text_scale`.
3. Use `st.components.v1.html` for embedded HTML (e.g. Markmap) if needed; keep assets under `references/` or a dedicated docs folder.

Technology explorations (PyGWalker, YData Profiling, DuckDB, PyDeck) are summarised in `docs/LEARNING_AND_BACKLOG.md`.
