<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# ADR-008: Multi-wave schema and mapping layer

- Status: Proposed
- Date: 2026-03-16

## Context

The Baromedr Cymru dashboard started life as a **single-wave** app (Wave 2) with a static Wave 1 context payload. As the project evolves, it needs to:

- incorporate **additional survey waves** over time; and
- keep **headline metrics and trends comparable** across waves, even when:
  - column names change between waves,
  - response options are added/removed/renamed,
  - some questions exist only in a subset of waves,
  - and future waves introduce more qualitative or mixed-format questions.

Today:

- `src/wave_context.py` defines a validated `WaveContext`/`WaveRegistry` model and a `TREND_METRICS` registry, and
- `build_wave_context_from_df` derives a Wave 2 context from a row-level DataFrame by calling into `src.eda` helpers.

This works well for Wave 2, but the derivation logic is **hand-wired to specific column names and assumptions**. Without a more explicit mapping layer, adding Wave 3+ would either:

- bake additional wave-specific conditionals into `build_wave_context_from_df`, or
- duplicate logic in new functions that risk drifting away from the core EDA behaviour and tests.

We want a more **declarative** and **auditable** way to map raw wave datasets onto a small, stable set of canonical metrics.

## Decision

Introduce a **per-wave schema and mapping layer** backed by small configuration files and thin Python helpers:

1. **Canonical metric IDs**
   - Treat the existing `TREND_METRICS` IDs and a small additional set of KPIs as the canonical surface for cross-wave comparison, e.g.:
     - Demand & finance:
       - `demand_increase`
       - `finance_deteriorated_costs`
       - `operating_likely`
       - `has_reserves`
       - `using_reserves`
     - Workforce & volunteering:
       - `has_volunteers`
       - `has_paid_staff`
       - `staff_rec_difficulty`
       - `staff_ret_difficulty`
       - `vol_rec_difficulty`
       - `vol_ret_difficulty`
       - `too_few_volunteers`
     - Concerns:
       - `income_top_concern`
       - `demand_top_concern`
       - `inflation_top_concern`
   - These IDs (not raw column names) are the stable “API” for trends, WaveContext, and Executive Summary narratives.

2. **Per-wave schema files**
   - For each wave, add a small configuration file under `config/waves/`, for example:
     - `config/waves/wave1.schema.yml`
     - `config/waves/wave2.schema.yml`
     - `config/waves/wave3.schema.yml` (future).
   - Each schema file describes:
     - **`meta`** – wave label and number:
       - `wave_label` (e.g. "Wave 2"),
       - `wave_number` (int, for ordering).
     - **`columns`** – how raw columns relate to conceptual questions, including:
       - nominal columns (e.g. `demand`, `financial`, `operating`),
       - basic metadata such as Likert order or “likely” subsets,
       - simple derived mappings (e.g. demand → `demand_direction` buckets).
     - **`metrics`** – how to compute canonical metrics from the raw/derived columns, using a small set of evaluation types (see below).

3. **Metric evaluation types**
   - Keep the mapping layer intentionally small and declarative. For most headline KPIs we only need a handful of patterns:
     - `share_eq`: percentage where a column equals a specific value, over a non-missing base.
     - `share_in`: percentage where a column is in a set of values.
     - `share_gt`: percentage where a numeric column exceeds a threshold.
     - `conditional_share`: percentage where some predicate holds **within** a conditioned subset (e.g. “using reserves among those that have reserves”).
   - Example (YAML sketch):
     - `demand_increase`:
       - from: `demand_direction`
       - type: `share_eq`
       - value: `Increased`
     - `has_volunteers`:
       - from: `peoplevol`
       - type: `share_gt`
       - threshold: 0
     - `using_reserves`:
       - type: `conditional_share`
       - condition: column `reserves` equals `Yes`
       - numerator: column `usingreserves` equals `Yes`

4. **Loader and helpers**
   - Implement a new module, e.g. `src/wave_schema.py`, that provides:
     - `load_wave_schema(wave_id: str) -> WaveSchema`:
       - reads and validates `config/waves/{wave_id}.schema.yml` into a Pydantic model (or equivalent),
       - caches per-process (similar to `load_la_context`).
     - Simple evaluation helpers:
       - `evaluate_share_eq(df, column, value) -> int`,
       - `evaluate_share_in(df, column, values) -> int`,
       - `evaluate_share_gt(df, column, threshold) -> int`,
       - `evaluate_conditional_share(df, condition, numerator) -> int`.
     - Optionally a convenience:
       - `evaluate_metric(df, metric_def) -> int`, dispatching on the metric `type`.

5. **Refactor WaveContext construction to use schemas**
   - Gradually adapt `build_wave_context_from_df` to:
     - call `load_wave_schema(f"wave{wave_number}")`,
     - use that schema to compute canonical metric values, and
     - plug those into `Meta`, `HeadlineFinancialHealth`, `DemandHeadline`, `WorkforceHeadline`, `OperationsHeadline`, `KeyOrganisationalConcerns`, and `RespondentProfile`.
   - For **Wave 2**, we will:
     - create a `wave2.schema.yml` that exactly matches the current behaviour; and
     - refactor `build_wave_context_from_df` to call through the schema while preserving existing calculations and denominators.
   - `TREND_METRICS` remains the registry of which canonical metrics are used for trends, but now relies on schema-backed values rather than hard-coded column logic.

6. **Handling missing or wave-specific metrics**
   - If a canonical metric does not exist for a given wave:
     - it can be omitted from that wave’s `metrics` section; evaluators should return `None` or skip those entries.
     - `trend_series`, `build_trend_long`, and `summarise_trend_changes` already skip missing values; they will continue to do so.
   - Wave-specific metrics that are not cross-wave comparable:
     - may still be present in per-wave schemas and surfaced on wave-specific pages or narratives,
     - but should **not** be added to `TREND_METRICS` unless they are comparable across at least two waves.

7. **Roadmap for Wave 3+**
   - When a new wave arrives:
     1. Make the new dataset resolvable via the existing runtime-data mechanisms (`resolve_dataset_source` or equivalents).
     2. Create `config/waves/waveN.schema.yml` describing raw columns and how to compute canonical metrics.
     3. Extend `build_wave_registry_from_current_data` to add a `WaveContext` for the new wave using `build_wave_context_from_df`.
     4. Decide, per canonical metric, whether the new wave supports it; update `TREND_METRICS` only where cross-wave comparability is sound.
     5. Add unit and integration tests to assert that schemas, WaveContext, and trends behave as expected.

## Consequences

### Positive

- **Multi-wave ready**: New waves can be onboarded primarily by updating a small declarative schema file, rather than editing multiple Python modules.
- **Cross-wave clarity**: The canonical metric IDs and per-wave schemas make it explicit which metrics are:
  - supported in which waves; and
  - genuinely comparable across waves.
- **Safer evolution**: Column renames or small wording changes in future surveys are handled via config rather than ad-hoc code paths.
- **Auditable**: The mapping from raw survey columns to executive metrics is visible and reviewable in `config/waves/` alongside tests and ADRs.
- **Testable**: Schema behaviour can be validated with small, fixture-based tests that ensure WaveContext and EDA-derived aggregates remain aligned.

### Negative / Trade-offs

- **Additional indirection**: Developers must understand the schema layer in addition to `wave_context` and `eda` when working on cross-wave metrics.
- **Configuration complexity**: There is a risk of over-configuration if we allow too many metric types or per-wave special cases; we mitigate this by keeping the evaluation vocabulary deliberately small.
- **Partial coverage**: Initially, only the metrics used in `WaveContext` and `TREND_METRICS` will be schema-driven; other analytics remain code-only until a need arises.

### Implementation plan

1. Add `config/waves/` and introduce a `wave2.schema.yml` that matches current Wave 2 behaviour.
2. Implement `src/wave_schema.py` with:
   - `WaveSchema` model,
   - `load_wave_schema`,
   - metric evaluation helpers,
   - and minimal unit tests.
3. Refactor `build_wave_context_from_df` to:
   - use `WaveSchema` for a subset of metrics (demand increase, finance deteriorated, has volunteers, has paid staff, reserves); and
   - validate via existing tests that values remain unchanged.
4. Once stable, extend schema usage to more metrics (e.g. concerns, recruitment difficulties) and update docs:
   - `docs/LEARNING_AND_BACKLOG.md` (multi-wave section),
   - `docs/learning/04_from_notebook_to_production.md` (“add a new wave” subsections).
5. When a real Wave 3 dataset is available, add its schema file and extend `build_wave_registry_from_current_data` to include it.
