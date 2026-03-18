<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# How to Read This Repo in 60–90 Minutes

This is a **guided tour** for someone with a Python / data‑science background
who wants to understand this codebase quickly and learn transferable patterns.

You can follow the same sequence when approaching other projects.

## 0–10 minutes: Orientation

1. **README.md**

   - Skim the top sections:

     - what the project is;
     - how to run the app (`streamlit run src/app.py`);
     - how to run tests;
     - where the docs live.

2. **docs/source/index.rst (HTML docs)**

   - Open the Sphinx docs (locally or on Read the Docs) and look at:

     - `Getting started`
     - `Architecture`
     - `Deployment checklist`.

## 10–25 minutes: Architecture and layout

1. **ARCHITECTURE.md**

   - Read the high-level flow:

     - `src/app.py` as the entry point;
     - `src/config.py`, `src/data_loader.py`, `src/eda.py` as the core;
     - `src/charts.py` and `src/section_pages/` for UI.

2. **docs/learning/01_repo_tour_for_python_data_scientists.md**

   - Skim to reinforce the mental model:

     - how this differs from notebook‑style work;
     - how tests and docs change expectations.

## 25–45 minutes: Follow a single request

1. **src/app.py**

   - Trace:

     - config and data load (`get_data`, `check_runtime_assets`);
     - sidebar filters and `apply_filters`;
     - `PageContext` construction;
     - page dispatch via `PAGE_RENDERERS` and `_run_page`.

2. **Pick one page**, e.g. `src/section_pages/overview.py`

   - See how it:

     - checks `suppressed`;
     - calls EDA helpers;
     - builds charts via `src.charts`;
     - links back to context (Wave trends, profile summary).

3. **Follow the EDA calls**

   - Open `src/eda.py` and locate the functions used by that page:

     - how they aggregate;
     - how they guard against missing columns or small bases.

## 45–65 minutes: Tests and invariants

1. **Unit tests for the modules you just saw**

   - `tests/unit/test_eda_core.py`
   - `tests/unit/test_eda_edge_cases.py`
   - `tests/unit/test_charts_core.py`
   - `tests/unit/test_filters.py`

   Look for:

   - which behaviours are considered stable;
   - how edge cases (empty data, NaNs) are handled.

2. **Integration tests**

   - `tests/integration/test_wave_context_integration.py`
   - `tests/integration/test_trend_series_integration.py`
   - `tests/integration/test_k_anonymity_end_to_end.py`
   - `tests/integration/test_demo_vs_real_modes.py`

   These show:

   - how cross‑module correctness is enforced;
   - how privacy (k‑anonymity) and demo vs real behaviour are tested.

## 65–80 minutes: Configuration, runtime, and ops

1. **src/config.py**

   - Scan:

     - runtime source resolution (`RuntimeDataSource`, `resolve_dataset_source`);
     - palettes and chart settings;
     - k‑anonymity constants;
     - label mappings and groupers.

2. **src/data_loader.py**

   - Understand:

     - `_read_csv_from_source` and logging;
     - `_clean` and `_derive_columns`;
     - `check_runtime_assets` and how it feeds **Deployment Health**.

3. **Deployment docs**

   - `docs/source/operations_runbook.rst`
   - `docs/source/privacy_and_suppression.rst`

   See how runtime behaviour maps to operator‑facing guidance.

## 80–90 minutes: Engineering patterns to reuse elsewhere

1. **docs/source/engineering_clusters_and_lifecycle.rst**

   - Read this as a **meta‑guide**:

     - architecture;
     - runtime robustness;
     - observability;
     - security/privacy;
     - testing;
     - performance;
     - docs and DX.

2. **docs/learning/06_feature_from_scratch_example.md**

   - Skim the worked example of adding a new feature/page end‑to‑end.
   - Use this as a template when you add your own features, here or in any
     other project.

At this point you should:

- understand how a request flows through the app;
- know where data comes from and how metrics are computed;
- see how privacy and robustness are enforced;
- have a concrete pattern you can apply to future SaaS/PaaS work.
