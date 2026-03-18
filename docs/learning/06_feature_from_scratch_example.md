<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Worked Example: Adding a Feature End‑to‑End

This guide shows how to add a new feature to this app following the
**engineering clusters + lifecycle** playbook. You can reuse the same steps
in any new SaaS/PaaS project.

## Scenario

You want to add a new **“Organisational Resilience”** page that:

- reuses existing Wave 2 metrics on finances, reserves, and demand;
- exposes a couple of new charts; and
- participates in the same k‑anonymity and observability rules as the rest of the app.

## 1. Clarify the feature

Write down, in 3–5 bullets:

- which user questions this page should answer (e.g. “How many orgs are using
  reserves?” “Is demand rising faster than capacity?”);
- which existing metrics you expect to reuse (e.g. `finance_deteriorated_pct`,
  `reserves_yes_pct`, `demand_pct_increased`);
- whether any new derived fields are needed (if yes, they probably belong in
  `src.eda.py`).

In this repo, those metrics already live in:

- `src.eda.workforce_operations()` and `demand_and_outlook()`
- `src.wave_context.WaveContext` and `TREND_METRICS`

## 2. Wire the new page (UI shell)

1. Create `src/section_pages/organisational_resilience.py` with:

   - a `render_page(ctx: PageContext) -> None` entrypoint;
   - one or more helper functions (`render_resilience_overview(ctx)`, etc.).

2. Register the page in:

   - `src/section_pages/__init__.py` (import the new module);
   - `src/navigation.py` (`NavItem` list);
   - `src/app.py` (`PAGE_RENDERERS` mapping).

Follow the pattern used by existing pages (Overview, Workforce & Operations).

## 3. Pull in domain metrics (EDA)

Identify which EDA helpers you need:

- For finances and reserves, reuse `workforce_operations(df)` and
  `demand_and_outlook(df)` from `src.eda.py`.
- If you need new aggregate logic:

  - implement it in `src.eda.py` next to related functions;
  - write unit tests in `tests/unit/test_eda_core.py` or `test_eda_edge_cases.py`.

Example pattern:

- Add `resilience_summary(df)` in `src.eda.py` that returns a dict of:

  - `finance_deteriorated_pct`
  - `reserves_yes_pct`
  - `demand_pct_increased`

- Test it with small fixtures so it is safe to call from pages and WaveContext.

## 4. Respect runtime robustness and privacy

On the new page:

- Accept the `PageContext` and use `ctx.df` (filtered view) for EDA.
- Check `ctx.ui_config.suppressed` at the top:

  - if `True`, show the same suppression warning and `st.stop()` pattern used
    on Overview and Executive Summary.

- Use the defensive EDA helpers:

  - they already handle missing columns and small‑n inputs; avoid re-implementing
    raw `value_counts()` inline without the same guards.

This keeps the new feature aligned with existing runtime robustness and privacy rules.

## 5. Add charts via shared helpers

Use `src.charts` helpers instead of custom Plotly code:

- `kpi_card_html` + `show_chart` for tiles and simple charts.
- `stacked_bar_ordinal`, `horizontal_bar_ranked`, `wave_trend_line` where appropriate.

This ensures:

- consistent palettes (`palette_mode` from `get_app_ui_config()`),
- alt‑text and accessibility text,
- optional data downloads (via `show_chart(..., data_df=...)`).

## 6. Tests

Add tests at two levels:

- **EDA**: verify new helper(s) in `src.eda.py` behave correctly for:

  - normal data,
  - empty frames,
  - frames missing some expected columns.

- **Integration** (optional): add a focused test that:

  - builds a small fixture DataFrame;
  - computes the new metrics; and
  - asserts they match the values used in any WaveContext fields or pages.

If the page has suppression behaviour, you can mirror the pattern in
`tests/integration/test_k_anonymity_end_to_end.py` to assert that it:

- warns when `suppressed=True`,
- calls `st.stop()` early.

## 7. Docs

Finally, update:

- `ARCHITECTURE.md` (one bullet under “section_pages” for the new page);
- if the page affects operators or privacy, mention it briefly in:

  - `docs/source/operations_runbook.rst` or
  - `docs/source/privacy_and_suppression.rst`.

This is the smallest repeatable skeleton for “new feature from scratch”:

1. Page shell + navigation.
2. EDA/domain logic.
3. Robustness and suppression.
4. Charts through shared helpers.
5. Tests for behaviour.
6. Docs for humans.

You can reuse the same outline in any new project: replace “Streamlit page” with
“API endpoint” or “frontend route”, but keep the layered approach the same.
