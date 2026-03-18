..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

Engineering clusters and product lifecycle
==========================================

This page is a **high-level playbook** for taking a data-heavy idea from
prototype to a robust SaaS/PaaS-style product.

It is grounded in this repository (WCVA Baromedr Cymru Wave 2 dashboard) but
written so that you can apply the same steps to any project – small or large –
without needing an AI assistant.

Use it as a checklist and as a map of “what to care about, and when”.

Related reference
-----------------

If you want a **capability map** view (a de-duplicated set of clusters you can use to
audit any software product), see :doc:`capability_clusters`.

1. Clarify the product and architecture
---------------------------------------

Goal: make sure you know **what problem** you are solving and **how the system
is shaped** before over-investing in code.

In this repo
^^^^^^^^^^^^

- :doc:`architecture` describes:

  - Entry point: ``src/app.py`` (Streamlit multipage shell).
  - Core layers:

    - ``src/config.py`` – configuration, palettes, label mappings, k-anonymity.
    - ``src/data_loader.py`` – data loading, cleaning, derived columns.
    - ``src/eda.py`` – analytical helpers and aggregates.
    - ``src/charts.py`` – chart primitives and accessibility.
    - ``src/section_pages/`` – page renderers.
    - ``src/wave_context.py`` – cross-wave registry and trend layer.

- ADRs under ``docs/adr/`` explain key choices (Streamlit UI, caching, multi-wave
  schema, Docker/CI).

How to generalise
^^^^^^^^^^^^^^^^^

- Pick a simple, explicit architecture early:

  - **Entry point / delivery**: web app, API, batch jobs, CLI, etc.
  - **Domain layer**: where core business rules live (EDA here).
  - **Infrastructure**: storage, queues, HTTP, UI framework.

- Write a short **architecture doc** (one page) that:

  - Names the modules/packages and what they own.
  - States constraints (privacy, latency, offline support, etc.).
  - Links to any ADRs for larger decisions.

This prevents you from “sprinkling logic everywhere” as the project grows.

2. Runtime robustness and configuration
---------------------------------------

Goal: the app should behave predictably in the face of missing data, partial
schemas, and misconfigurations.

In this repo
^^^^^^^^^^^^

- ``src/config.py``:

  - Centralises paths, environment/secret lookups, and runtime source resolution
    via ``RuntimeDataSource`` and helpers like ``resolve_dataset_source()``.
  - Implements demo mode vs real mode and URL masking.

- ``src/data_loader.py``:

  - Wraps CSV reading and derived-column creation.
  - Raises clear ``FileNotFoundError`` / ``RuntimeError`` with masked details.

- ``src/app.py``:

  - Uses ``get_data()`` with `try/except` to show friendly dataset load errors.
  - Implements a per-page error boundary so one broken chart does not kill the
    entire app.
  - Applies global k-anonymity suppression before rendering sensitive pages.

- ``src/eda.py`` and ``src/wave_context.py``:

  - Treat missing columns and small-n frames defensively (returning empty
    or zero-valued structures instead of raising).
  - Omit Wave 2 from trends when there is insufficient data.

How to generalise
^^^^^^^^^^^^^^^^^

- Centralise configuration and runtime sources:

  - One module for env vars, secret lookups, and path/URL resolution.
  - A small value object (like ``RuntimeDataSource``) that describes:

    - Where a resource came from.
    - Whether it exists.
    - Whether it is demo/test vs production.

- Add **guardrails** at the outer edges:

  - Fail early and clearly when mandatory data cannot be loaded.
  - Check base sizes and schema presence before running heavy logic.
  - Use feature flags or config toggles for risky behaviour, not ad hoc ``if``.

3. Observability
----------------

Goal: be able to answer “what is the app doing in production?” without guesswork.

In this repo
^^^^^^^^^^^^

- ``src/config.py``:

  - Defines ``WCVA_LOGGER`` via ``get_wcva_logger()``, the single logger for
    the app.

- ``src/data_loader.py`` and ``src/wave_context.py``:

  - Log dataset source decisions, CSV read errors, and WaveContext registry
    construction (waves present, data sizes, reasons for omitting Wave 2).

- ``src/section_pages/deployment_health.py``:

  - Surfaces asset checks and runtime modes in a human-readable UI.
  - Allows downloading JSON and CSV snapshots for offline debugging.

How to generalise
^^^^^^^^^^^^^^^^^

- Choose a **single logging entry point** (per service) and stick to it.
- Log:

  - Configuration decisions (which dataset/URL was used).
  - Resource sizes (rows, columns, items).
  - Reasons for falling back to demo/test modes.

- Provide an **operator-friendly surface**:

  - A health/diagnostics endpoint or page.
  - Optional JSON export for attaching to tickets.

4. Security and privacy
-----------------------

Goal: protect users and organisations by design, not as an afterthought.

In this repo
^^^^^^^^^^^^

- ``src/config.py`` and ``src/data_loader.py``:

  - Treat dataset and LA context URLs as secrets; log only masked forms.
  - Warn on non-HTTPS URLs.

- ``src/config.py`` and ``src/app.py``:

  - Implement and consistently use a k-anonymity threshold
    (``K_ANON_THRESHOLD`` and ``ui_config.suppressed``).

- Docs:

  - ``docs/learning/02_private_data_secrets_and_demo_mode.md`` – secrets/env
    hygiene and demo mode.
  - :doc:`privacy_and_suppression` – user-facing explanation of suppression and
    disappearing slices.
  - :doc:`operations_runbook` – how to fix misconfigurations without leaking data.

How to generalise
^^^^^^^^^^^^^^^^^

- Decide early:

  - What counts as **private** (dataset contents, URLs, IDs).
  - What your **minimum base** is for showing segment-level data.

- Apply privacy rules consistently:

  - Compute suppression flags centrally.
  - Make every view respect those flags where appropriate.
  - Mask sensitive values in logs and UIs (paths, URLs, IDs).

- Document:

  - What suppression means.
  - That disappearing slices are intentional, not a bug.

5. Testing depth
----------------

Goal: use tests not only to catch regressions, but to **encode invariants** of
your product.

In this repo
^^^^^^^^^^^^

- Unit tests for:

  - Core EDA helpers (including property-based tests for percentages and ranges).
  - Filters, narratives, charts, navigation, WaveContext schema models.

- Integration tests for:

  - WaveContext vs EDA alignment.
  - Trends and Wave registry behaviour with missing/partial data.
  - k-anonymity behaviour on page renderers.
  - Demo vs real mode resolution and Deployment Health.

How to generalise
^^^^^^^^^^^^^^^^^

- Start with a minimal but **representative** fixture dataset or domain object.
- Write tests that:

  - Assert key metrics agree across layers (e.g. raw data vs aggregate vs
    presentation models).
  - Cover edge cases: empty data, small-n, missing columns, surprising inputs.
  - Reflect privacy rules (suppression, masking).

- Use property-based testing (e.g. Hypothesis) where invariants are numeric or
  structural (percentages in [0, 100], sums ≈ 100, monotonicity).

6. Performance and UX
---------------------

Goal: keep the app responsive and explain trade-offs to users.

In this repo
^^^^^^^^^^^^

- ``src/data_loader.py``:

  - Uses caching for LA context via ``@lru_cache``.

- ``src/wave_context.py``:

  - Uses ``@st.cache_data`` for wave registry construction.

- Section pages:

  - Truncate large tables (e.g. trends, Deployment Health assets, Data Notes
    block completeness) and offer CSV downloads for full data.

How to generalise
^^^^^^^^^^^^^^^^^

- Profile early where it hurts:

  - Expensive joins, large aggregations, or repeated per-request work.

- Cache or precompute:

  - Small, stable reference tables.
  - Slow but deterministic aggregates.

- In the UI:

  - Cap rows/columns to a sensible maximum.
  - Always provide a way to download the full result (CSV, JSON).
  - Be honest in captions about truncation.

7. Documentation and learning journey
-------------------------------------

Goal: make the codebase teach itself to the next person (or to you in six months).

In this repo
^^^^^^^^^^^^

- **Top-level docs**:

  - ``README.md`` – overview, install, run, docs, testing, deployment.
  - ``ARCHITECTURE.md`` – flow and module-level design.
  - ``CONTRIBUTING.md`` – dev standards, including typing and docs.

- **Sphinx docs** (:doc:`index`):

  - Getting started, architecture, contributing, API reference.
  - :doc:`deployment_checklist`, :doc:`operations_runbook`,
    :doc:`privacy_and_suppression`, this page.

- **Learning guides**:

  - ``docs/learning/`` – step-by-step guides to private data, secrets, demo
    mode, deployment, testing, and git practices rooted in this repo.

How to generalise
^^^^^^^^^^^^^^^^^

- Maintain three layers of docs:

  1. **README** – for new arrivals.
  2. **Architecture + operations** – system-level concepts and runbooks.
  3. **API / module docs** – for maintainers and library-style reuse.

- Keep docs and code in sync:

  - When behaviour changes (e.g. data loading, suppression, demo mode), update
    the relevant doc section as part of the same change.

8. Developer experience (DX)
----------------------------

Goal: make it easy to work on the project safely and consistently.

In this repo
^^^^^^^^^^^^

- ``pyproject.toml``:

  - Configures Black, isort, and mypy (with stricter overrides for core modules).

- ``.pre-commit-config.yaml``:

  - Trailing whitespace, EOF, YAML checks, large-file guard, and private-key
    detection.
  - isort + Black + pytest (non-e2e) + mypy hooks.
  - Commented, opt-in hooks for pyupgrade and a secrets detector.

- ``pytest.ini``:

  - Clear markers for e2e tests vs unit/integration.

How to generalise
^^^^^^^^^^^^^^^^^

- Add a small number of **automatic checks**:

  - Code formatting (Black or equivalent).
  - Imports (isort or similar).
  - Type checks (mypy or similar, at least on core modules).
  - Tests (or at least a smoke subset).

- Use pre-commit hooks for local fast feedback and mirror them in CI.
- Tighten type checking and linting gradually, starting with the most important
  modules (configuration, data loading, domain logic).

Putting it together as a lifecycle
----------------------------------

When starting a new SaaS/PaaS project, you can walk this playbook in phases:

1. **Vision and architecture**

   - Write a short problem statement and rough architecture.
   - Decide entry points, domain layer, and data sources.

2. **Baseline implementation**

   - Implement the simplest end-to-end slice: data in → minimal UI/API out.
   - Add just enough tests to fix the behaviour.

3. **Runtime robustness + observability**

   - Centralise config and data sources.
   - Add logging and a health/diagnostics surface.

4. **Privacy and security**

   - Decide suppression and masking rules.
   - Apply them consistently across views and logs.

5. **Testing and performance**

   - Extend unit and integration tests to cover edge cases and invariants.
   - Cache or precompute heavy, stable work; add truncation + downloads in the UI.

6. **Docs and DX**

   - Document how to run, test, and deploy.
   - Add pre-commit and type checking.
   - Gradually refine docs and ADRs as behaviour stabilises.

You can revisit each cluster whenever the product grows or changes. In this
repo, we followed exactly this pattern – starting from a working Streamlit
dashboard and iteratively tightening runtime behaviour, observability, privacy,
testing, performance, documentation, and developer experience.
