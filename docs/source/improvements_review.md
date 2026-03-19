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
- **Quality gates exist and are automated**: CI covers tests, Ruff lint/format checks, import-linter architecture contracts, mypy, security scans, packaging validation, and docs build.
- **Documentation is treated as a product artefact**: Sphinx site with architecture, operations, privacy/suppression, lifecycle guidance.

The biggest opportunities are now mostly “maturity” improvements:

- **Make the release process canonical and checklist-driven** (single source of truth, cross-linked from README/Contributing/Sphinx).
- **Reduce duplication/inconsistency across pages** (a few pages have duplicated docstrings or different suppression patterns).
- **Codify performance/caching boundaries** (what is cached, why, and how filters affect computation).
- **Turn broad knowledge (capability clusters) into a concise, navigable reference** linked to this repo’s concrete practices.

## Assessment: professionalisation and maturation debt

This section captures the outcome of external and internal reviews focussing on intentional engineering principles with normal maturation debt. It also records a high-signal, low-noise roadmap to fully professionalise the repo.

### Verdict

It is **professionally minded and intentionally engineered**, with explicit architecture (ARCHITECTURE.md, ADRs), substantive CI (tests, lint, types, security, packaging, docs), test stratification (unit, integration, e2e), architectural enforcement (import-linter, nav→dispatch test), and serious attention to privacy (demo mode, k-anonymity, URL redaction). The weak spots below are **conventional single-product / organically-grown debt**.

### Findings from review (March 2026)

**1. Medium — UI/rendering layer enforcement is thinner than the docs suggest**

- Overall coverage is modest (~60%); several high-change presentation modules are barely exercised.
- Page modules with weak or no direct test coverage include: `src/section_pages/overview.py`, `src/section_pages/at_a_glance.py`, `src/section_pages/trends_and_waves.py`, and `src/generate_presentation.py`.
- Core analytics (config, data_loader, eda, charts) are better protected; the presentation layer is guarded mainly by e2e smoke tests.
- The current repo-wide coverage gate is still permissive enough that the suite can pass while important presentation-heavy modules remain lightly tested.
- **Direction**: Add targeted unit-style tests for data-selection and metric logic used by these pages (even if Streamlit itself is not fully exercised), and/or raise coverage goals for key section pages where safe.

**2. Medium — Large multi-responsibility modules**

- Several important modules have grown into large, multi-responsibility files (organic evolution rather than a fully matured modular design).
- Affected modules: `src/config.py`, `src/wave_context.py`, `src/eda.py`, `src/generate_presentation.py`.
- **Direction**: Split by sub-domain over time (e.g. config/runtime vs config/ui; eda/demand vs eda/volunteering; presentation/html vs presentation/pdf) to improve boundaries and cognitive load.

**3. Low — Packaging/import hygiene**

- Both `src/app.py` and `src/generate_presentation.py` modify `sys.path` at import time so the project root is on the path. This is a pragmatic workaround common in repos that started as scripts and were later professionalised.
- **Direction**: Remove the need for `sys.path` manipulation by relying on an installable package or a consistent entry point (e.g. `python -m ...`) so that CLI, tests, and packaging all use the same import semantics.

**4. Low — Narrow architectural contracts**

- The import-linter config (`.importlinter`) currently enforces only two contracts, both centred on `section_pages`. Useful, but not yet a broad architectural safety net.
- **Direction**: Broaden contracts (e.g. section_pages must not import low-level infra directly; tests must not depend on section_pages except via a defined surface; encode more of ARCHITECTURE.md layering into import rules).

**5. Additional improvement areas**

- **Page modules as thin presenters**: Move non-trivial data shaping from section pages into `eda.py` or helpers so page modules are thin presenters; add unit-style tests for any logic that remains in page modules.
- **Typed boundaries**: Introduce small dataclasses or TypedDicts at the boundary between `eda` and `section_pages` so the UI layer has clear contracts instead of generic dicts.
- **Observability**: Use `WCVA_LOGGER` consistently with structured keys (e.g. dataset_source_type, app_mode, n_rows) around data-source resolution, filter application, and key user actions; centralise “required assets present” checks so they can be asserted in tests as well as on the deployment health page.
- **UI automation maturity**: The current e2e layer is intentionally light and import-oriented. If the dashboard becomes more user-facing or design-sensitive, add browser-driven UI automation for key flows (navigation, filters, suppression messaging, demo-mode labelling, chart/table toggles, download affordances) rather than relying only on import smoke plus unit/integration coverage.

These items are reflected in the prioritised backlog below where they are not already covered.

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
  - **Acceptance**: consistent structured keys; no raw URLs in logs; key user actions are represented explicitly (for example: filter changes, mode switches, and page render failures).

- **UI/rendering layer test depth**
  - **Where**: add targeted unit-style tests for data-selection and metric logic used by `src/section_pages/overview.py`, `src/section_pages/at_a_glance.py`, `src/section_pages/trends_and_waves.py`, and (where feasible) `src/generate_presentation.py`; avoid relying solely on e2e smoke for presentation logic.
  - **Why**: these high-change modules are currently barely exercised; tests guard refactors and prevent regressions.
  - **Acceptance**: meaningful coverage or explicit tests for key page-level metric/build logic; coverage threshold or module-level goals updated so the suite cannot pass indefinitely with thin coverage in presentation-heavy modules.

- **Eliminate sys.path manipulation**
  - **Where**: `src/app.py` and `src/generate_presentation.py` currently insert the project root into `sys.path` at import time.
  - **Why**: packaging hygiene; run identically from CLI, tests, and installed package without path hacks.
  - **Acceptance**: entry points work via `python -m ...` or installed package; no `sys.path` modification in app or presentation code.

- **Broaden import-linter contracts**
  - **Where**: `.importlinter`; currently only two contracts, both centred on `section_pages`.
  - **Why**: encode more of ARCHITECTURE.md layering (e.g. section_pages do not import low-level infra directly; tests use a defined surface for section_pages).
  - **Acceptance**: at least one additional contract that reinforces app → pages → eda/data boundaries; docs updated.

- **Browser-driven UI regression coverage**
  - **Where**: add a small, stable browser E2E layer alongside the current smoke tests; Playwright is a strong candidate if the team wants full user-journey automation.
  - **Why**: some risks only appear in the real browser/runtime interaction layer, such as broken sidebar navigation, widgets not retaining state, suppression banners not appearing when filters shrink the sample, demo-mode labelling regressions, broken embedded HTML, layout issues, or download controls disappearing.
  - **How to keep it proportionate**: start with a tiny happy-path suite rather than a broad brittle UI matrix. Focus on a few canonical journeys and stable assertions, using the bundled sample dataset or explicit demo mode.
  - **Suggested initial scenarios**:
    - app boots and shows the expected default page in demo/sample mode
    - sidebar navigation switches between a few core pages successfully
    - applying filters can trigger the suppression warning and hide sensitive outputs
    - deployment health page shows runtime-source state and demo/real labelling
    - a representative page still renders key charts/tables after filter changes
  - **Acceptance**: CI runs a small browser-based regression suite reliably; failures correspond to user-visible breakage rather than cosmetic noise.

### P2 — Longer-term / optional

- **Task runner for DevEx**
  - **Where**: add a lightweight `Makefile` or `justfile` with tasks: `fmt`, `test`, `typecheck`, `docs`, `ci-local`.
  - **Acceptance**: new contributors can run the whole local workflow reliably.

- **Multi-wave mapping layer expansion**
  - **Where**: follow ADR-008; expand `config/waves/*.schema.yml` and evaluator vocabulary in `src/wave_schema.py`.
  - **Acceptance**: new waves can be added with minimal code changes and robust comparability checks.

- **Split large multi-responsibility modules**
  - **Where**: `src/config.py`, `src/wave_context.py`, `src/eda.py`, `src/generate_presentation.py` each carry many distinct responsibilities.
  - **Why**: improve boundaries and cognitive load; e.g. `config/` (runtime vs UI), `eda/` (demand, volunteering, etc.), `presentation/` (html vs pdf).
  - **Acceptance**: submodules or packages with clear single-purpose modules; public API preserved or explicitly migrated.

- **Thin presenters and typed boundaries**
  - **Where**: `src/section_pages/*`; move non-trivial data shaping into `src/eda.py` or helpers; introduce small dataclasses or TypedDicts at the `eda` ↔ `section_pages` boundary.
  - **Why**: page modules become thin presenters; UI layer has clear contracts instead of generic dicts; easier to test and refactor.
  - **Acceptance**: section pages call EDA helpers that return typed structures; no ad-hoc dict building in page renderers for complex data.

- **Testing strategy overhaul (if UI complexity grows)**
  - **Where**: test pyramid across `tests/unit`, `tests/integration`, and browser E2E.
  - **Why**: if the product becomes more operator-facing or visually richer, the current testing strategy may remain too backend-heavy relative to actual UX risk.
  - **Direction**:
    - keep most logic tests at unit/integration level for speed and debuggability
    - use browser E2E only for a narrow set of critical user journeys
    - add visual/assertion helpers only for intentionally stable UI elements, not every chart pixel
    - prefer deterministic demo/sample fixtures and explicit runtime modes for repeatability
  - **Acceptance**: the repo has a documented test pyramid that explains what belongs in unit, integration, smoke, and browser-E2E layers, with CI scope sized to remain fast and reliable.

## How to use this backlog

- Use this as a **review template** for future work: when a new feature is added, tick off the clusters it touches and add the missing guardrails early.
- Keep it **proportionate**: avoid adding enterprise-grade process unless it clearly reduces risk or improves usability for operators and analysts.
