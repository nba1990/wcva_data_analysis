---
title: Comprehensive review and improvement backlog
---

# Comprehensive review and improvement backlog

This page turns a broad “review the whole codebase” request into two practical outputs:

- **Audit checklist**: a capability-cluster view of what is present, what is missing, and what to improve.
- **Prioritised backlog**: concrete, repo-specific work items with file pointers and acceptance notes.

This is grounded in this repository, but phrased so the same review method can be reused elsewhere.

## Executive summary (current state)

This repo is already unusually strong for a data-heavy Streamlit dashboard:

- **Operational robustness is first-class**: explicit demo mode, runtime source resolution, deployment health UI, operator runbook.
- **Quality gates exist and are automated**: CI covers tests, lint (Black/isort), import-linter architecture contracts, mypy, pip-audit, docs build.
- **Documentation is treated as a product artefact**: Sphinx site with architecture, operations, privacy/suppression, lifecycle guidance.

The biggest opportunities are now mostly “maturity” improvements:

- **Make the release process canonical and checklist-driven** (single source of truth, cross-linked from README/Contributing/Sphinx).
- **Reduce duplication/inconsistency across pages** (a few pages have duplicated docstrings or different suppression patterns).
- **Codify performance/caching boundaries** (what is cached, why, and how filters affect computation).
- **Turn broad knowledge (capability clusters) into a concise, navigable reference** linked to this repo’s concrete practices.

## Audit checklist (capability clusters)

This uses the umbrella capability clusters described in `capability_clusters` (see that page for definitions).

For each cluster:

- **Evidence in this repo**: high-signal links.
- **Gaps / risks**: what’s missing or likely to bite later.
- **Improvements**: changes that are proportionate for this project.

### 1) Product_and_strategy

- **Evidence in this repo**:
  - Project overview and structure: `README.md`.
  - Policy questions and future direction: `plans/policy_questions.md`, `docs/LEARNING_AND_BACKLOG.md`.
- **Gaps / risks**:
  - No explicit “north-star outcomes” (what success looks like for operators vs analysts vs stakeholders).
- **Improvements**:
  - Add a short “Goals and non-goals” section to `README.md` or `ARCHITECTURE.md` (keep it concise).

### 2) User_experience_and_adoption

- **Evidence in this repo**:
  - Accessibility toggles: `src/app.py` (`Colour-blind friendly palette`, chart text scaling).
  - Alt-text plumbing: `src/charts.py` (via `show_chart`) and tests (`tests/unit/test_charts_core.py`).
- **Gaps / risks**:
  - UX behaviour can drift across pages (slightly different suppression messaging, chart/table toggles).
- **Improvements**:
  - Centralise common page scaffolding patterns (title/caption/suppression stop/section dividers) to reduce drift.

### 3) Functional_capabilities

- **Evidence in this repo**:
  - Section pages: `src/section_pages/`.
  - Analysis core: `src/eda.py`, `src/wave_context.py`.
- **Gaps / risks**:
  - As features grow, metric definitions can fragment between dashboard and presentation generator.
- **Improvements**:
  - Keep metric definitions “single-source” in `src/eda.py` / `src/wave_context.py`; treat `src/generate_presentation.py` as a consumer only.

### 4) Architecture_and_engineering

- **Evidence in this repo**:
  - Architecture overview: `ARCHITECTURE.md`, Sphinx `docs/source/architecture.rst`.
  - ADRs: `docs/adr/ADR-00*.md`.
  - Import linter contracts: `.importlinter`, `docs/source/architecture/contracts.md`.
- **Gaps / risks**:
  - Some section page modules include duplicated docstrings; minor consistency debt.
- **Improvements**:
  - Add a small “section page contract” doc (inputs/outputs, suppression handling, chart helper usage).

### 5) Data_and_integration

- **Evidence in this repo**:
  - Runtime source resolution + masking: `src/config.py`, `src/data_loader.py`.
  - LA context loading and caching: `src/data_loader.py`.
- **Gaps / risks**:
  - Schema drift in private datasets: currently handled defensively, but validation could be clearer.
- **Improvements**:
  - Add an optional schema validation step (e.g. expected columns + types) that produces a redacted diagnostic report for operators.

### 6) Security_privacy_and_trust

- **Evidence in this repo**:
  - Masking for URLs: `src/config.py:mask_runtime_value`.
  - k-anonymity suppression: `src/app.py` sets `ui_config.suppressed`; pages stop early.
  - Secrets guidance: `docs/learning/02_private_data_secrets_and_demo_mode.md`, `docs/HISTORY_REWRITE_AND_STREAMLIT_SECRETS.md`.
- **Gaps / risks**:
  - Suppression enforcement is implemented per page; any new page could forget it.
- **Improvements**:
  - Provide a single helper for “suppression gate” and require all pages to use it (backed by a test).

### 7) Reliability_performance_and_scalability

- **Evidence in this repo**:
  - Caching dataset load: `src/app.py` uses `@st.cache_data` on `get_data()`.
  - Cached wave registry: `src/wave_context.py` uses `@st.cache_data`.
  - Cached SROI mind-map HTML: `src/section_pages/sroi_references.py` uses `@st.cache_data`.
- **Gaps / risks**:
  - Filter changes can trigger repeated EDA computations; some pages recompute similar aggregates.
- **Improvements**:
  - Define “expensive aggregates” boundaries and cache at the right layer (EDA outputs keyed by filter selections, where safe).

### 8) Observability_operations_and_service_management

- **Evidence in this repo**:
  - In-app diagnostics: `src/section_pages/deployment_health.py`.
  - Operator runbook: `docs/source/operations_runbook.rst`.
  - Deployment checklist: `docs/source/deployment_checklist.md`.
- **Gaps / risks**:
  - Logging is present but could be more consistently structured across modules.
- **Improvements**:
  - Standardise structured logging keys (dataset_source_type, app_mode, n_rows, n_cols, filter_base_n).

### 9) Platform_infrastructure_and_delivery

- **Evidence in this repo**:
  - Docker guidance: `docs/DOCKER_AND_DEPLOYMENT.md`, ADR-005.
  - CI coverage: `.github/workflows/ci.yml`, ADR-006.
  - Read the Docs: `.readthedocs.yaml`, `docs/source/conf.py`.
- **Gaps / risks**:
  - Release steps exist but are not yet a single canonical runbook.
- **Improvements**:
  - Add `release_process` (see that page) and reference it from `CONTRIBUTING.md` and `README.md`.

### 10) Quality_governance_and_compliance

- **Evidence in this repo**:
  - Tests: `tests/` (unit + integration + e2e smoke).
  - Property-based tests (Hypothesis): `tests/unit/test_eda_properties.py`.
  - Security scanning: `pip-audit` job in `.github/workflows/ci.yml`.
- **Gaps / risks**:
  - A few UI contracts are hard to test without smoke/integration scaffolding.
- **Improvements**:
  - Add small integration tests for “page suppression gate used” and “no private URL leakage in rendered diagnostics”.

### 11) Developer_enablement_and_ways_of_working

- **Evidence in this repo**:
  - Contributor workflow: `CONTRIBUTING.md`, `docs/source/contributing.rst`.
  - Learning guides: `docs/learning/`.
  - Pre-commit config exists: `.pre-commit-config.yaml`.
- **Gaps / risks**:
  - Local “one-liner” workflow could be clearer (setup, run checks, build docs).
- **Improvements**:
  - Add a short `make`/`just`-style task runner (optional) or a single “Local CI checklist” snippet in `CONTRIBUTING.md`.

### 12) Commercial_customer_and_org_success

- **Evidence in this repo**:
  - Not a commercial product; but operator and stakeholder support exists via docs and runbooks.
- **Gaps / risks**:
  - N/A for this repo (keep it proportionate).
- **Improvements**:
  - Maintain the “operator friendly” posture: health page + runbooks + redacted diagnostics.

## Prioritised backlog (repo-specific)

Priority labels are “P0” (high leverage/low risk), “P1” (medium), “P2” (longer-term / optional).

### P0 — Quick wins / risk reducers

- **Canonical release runbook** (single source of truth)
  - **Where**: add `docs/source/release_process.md`; link from `docs/source/index.rst`, `CONTRIBUTING.md`, and `README.md`.
  - **Why**: reduces drift and makes releases repeatable.

- **Suppression enforcement helper**
  - **Where**: likely `src/page_context.py` (or a tiny `src/page_helpers.py`) + update all `src/section_pages/*`.
  - **Why**: prevents accidental leakage when new pages are added.
  - **Acceptance**: new integration test fails if any page forgets to gate on suppression.

- **Remove duplicated docstrings / minor consistency debt**
  - **Where**: e.g. `src/section_pages/trends_and_waves.py`, `src/section_pages/concerns_and_risks.py` show duplicated “Render … page” strings.
  - **Why**: reduces noise and makes docs generation cleaner.

### P1 — Solid improvements

- **Performance: cache expensive EDA aggregates**
  - **Where**: EDA functions in `src/eda.py` that are called repeatedly per rerun; consider caching keyed by stable inputs (e.g. filter selections) rather than raw DataFrames.
  - **Acceptance**: measurable reduction in runtime for common filter changes; no stale data surprises.

- **Schema validation and redacted diagnostics for operators**
  - **Where**: `src/data_loader.py` after `_clean` / `_derive_columns`; report in `deployment_health` page.
  - **Acceptance**: clear, redacted warnings when expected columns are missing; app still boots in demo mode where appropriate.

- **Logging consistency**
  - **Where**: `src/data_loader.py`, `src/wave_context.py`, `src/app.py`, `src/generate_presentation.py`.
  - **Acceptance**: consistent structured keys; no raw URLs in logs.

### P2 — Longer-term / optional

- **Task runner for DevEx**
  - **Where**: add a lightweight `Makefile` or `justfile` with tasks: `fmt`, `test`, `typecheck`, `docs`, `ci-local`.
  - **Acceptance**: new contributors can run the whole local workflow reliably.

- **Multi-wave mapping layer expansion**
  - **Where**: follow ADR-008; expand `config/waves/*.schema.yml` and evaluator vocabulary in `src/wave_schema.py`.
  - **Acceptance**: new waves can be added with minimal code changes and robust comparability checks.

## How to use this backlog

- Use this as a **review template** for future work: when a new feature is added, tick off the clusters it touches and add the missing guardrails early.
- Keep it **proportionate**: avoid adding enterprise-grade process unless it clearly reduces risk or improves usability for operators and analysts.
