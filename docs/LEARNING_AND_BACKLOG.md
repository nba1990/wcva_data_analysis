# Learning and Backlog

This document captures backlog items, testing strategy notes, and pointers to policy questions and plans so that knowledge from past planning and development remains actionable. **New or returning?** The main **README** has a short "New here? Picking this up again?" orientation and a "Documentation index" table listing all key docs (this file, ARCHITECTURE, CONTRIBUTING, ADRs, Sphinx, etc.).

---

## 1. Backlog (future enhancements)

These items were identified during architecture and testing work; they are **not** required for the current dashboard but are useful for future work.

### 1.1 Technology exploration

- **PyGWalker / YData Profiling**  
  Evaluate for rapid EDA inside the dashboard (e.g. a separate “EDA playground” page for internal use). Would allow interactive exploration of columns and distributions without writing custom Streamlit widgets.

- **DuckDB**  
  Assess whether DuckDB would simplify heavy analytical queries (e.g. aggregations over large slices, cross-wave joins) currently implemented in Pandas. Could reduce memory use and speed up some filters.

- **PyDeck**  
  Consider a small geospatial view if geographic data (local authorities, regions) becomes central to a story—e.g. overlay Baromedr results on a Wales map.

### 1.2 Future dashboards (portfolio-style)

- **Retrofit Impact Dashboard** – Impact of retrofit/energy efficiency programmes (if data becomes available).
- **Fuel Poverty Risk Map** – Geospatial view of fuel poverty risk by area, optionally overlaying voluntary sector presence.
- **Community Energy Investment Simulator** – Exploratory idea; no current implementation.

These can be separate apps or new pages; the same patterns (section page, nav item, shared chart helpers, optional Markmap/HTML embed) apply.

---

## 2. CI and test runs

- **GitHub Actions** – On every push and pull request, the workflow in `.github/workflows/ci.yml` runs:
  - **Tests**: `pip install -r requirements.txt` then `pytest tests/ -m "not e2e"` on Python 3.11 and 3.12 (e2e tests are excluded in CI).
  - **Lint**: `black --check` and `isort --check-only` on `src/` and `tests/`.
- The project uses **pip** and **`requirements.txt`** (no Conda). Test discovery and the `e2e` marker are configured in `pytest.ini`; Black and isort settings are in `pyproject.toml`.
- The rationale for a single workflow, pip, and the e2e marker is recorded in **ADR-006** (`docs/adr/ADR-006-ci-and-testing.md`).

---

## 3. Testing strategy (from plans)

Summary of how tests are structured and what they guard:

- **Unit tests** – Pure logic in `data_loader`, `eda`, `wave_context`, infographic/narrative helpers. Use small in-memory DataFrames and fixtures.
- **Integration tests** – WaveContext + EDA consistency, trend/registry behaviour, infographic metric builders with Wave 1 vs Wave 2 comparisons.
- **Regression tests** – Fixture-based (e.g. `wcva_sample_dataset.csv`) to pin headline metrics used on Overview/Executive pages. See `tests/unit/test_metrics_executive_overview.py`.
- **Navigation tests** – Uniqueness of nav IDs and wiring to `app.py` dispatch. See `tests/unit/test_navigation.py`.
- **SROI chart tests** – Each factory returns a `go.Figure` with titles; `palette_mode` and `text_scale` change colours and font sizes. See `tests/unit/test_sroi_figures.py`.

The fixture CSV must use **raw** questionnaire columns so `load_dataset()` can run `_clean` and `_derive_columns`; keep it in sync with `data_loader` and `eda` column expectations. The file `tests/fixtures/wcva_sample_dataset.csv` also includes multi-select columns (`concerns_1`, `concerns_2`, `actions_10`, `vol_recmethods_1`, `vol_recbarriers_1`, `vol_retbarriers_1`) so that `executive_highlights()` and Overview/Executive tests run without skipping.

### 3.1 Documentation and typing

Modules and public APIs are documented with docstrings (summary; Args and Returns for functions). Type hints are used on function parameters and return values. See `CONTRIBUTING.md` §7 for the full standard. When adding code, mirror the style in `src/data_loader.py`, `src/config.py`, and `src/eda.py`. EDA and data_loader use `dict[str, Any]` / `list[dict[str, Any]]` for return types so mixed value types (DataFrames, scalars, nested dicts) stay mypy-clean.

### 3.2 Test coverage

Coverage is run with: `pytest tests/ -m "not e2e" --cov=src --cov-report=term-missing`. The goal is **meaningful** coverage of core logic (data loading, EDA, config helpers, charts, narratives, navigation), not 100%. Expected gaps:

- **`app.py`** and **section page `render_*`** – Streamlit UI; covered by e2e smoke tests, not unit tests.
- **`generate_presentation.py`**, **`debug_metrics.py`** – CLI/standalone scripts; optional to cover.
- **`navigation.render_sidebar_nav`** – Depends on `st.session_state` and widgets; covered by e2e.

Adding tests: prefer unit tests for pure functions and EDA/data_loader; use mocks for functions that depend on Streamlit (e.g. `executive_highlights` with mocked EDA helpers) when you need to assert output structure.

---

## 4. Policy questions and plans

- **`plans/policy_questions.md`** – High-priority policy questions for WCVA teams (volunteer recruitment, retention, demand/finance, geography, earned settlement, methodology). Use for Wave 3 design and stakeholder conversations.
- **Cursor/plan documents** – Historical plans (e.g. SROI references page, testing strategy, architecture and testing) are under `.cursor/plans/`. Their content has been folded into:
  - `ARCHITECTURE.md` (flow, modules, tour, future dashboards),
  - `README.md` (quickstart, testing, deployment),
  - `CONTRIBUTING.md` (development setup, pre-commit, PR guidelines),
  - `CHANGELOG.md` (version history),
  - `docs/adr/` (ADR-001–006),
  - This file (backlog, testing notes, policy reference).

---

## 5. Safe vs unsafe patterns (recap)

- **Safe**: `st.session_state` and small dataclasses for per-user state; `st.cache_data` for read-only data; immutable config and palettes in `config.py`.
- **Unsafe**: Mutable module-level globals updated per request; open connections/cursors in globals without a clear lifecycle.

See ADR-004 and the “Multi‑user and session model” section in `ARCHITECTURE.md` for full detail.
