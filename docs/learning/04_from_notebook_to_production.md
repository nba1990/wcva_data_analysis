<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

## From Notebook to Production in This Repo

This guide walks through a concrete path from **“I have a CSV and an exploratory notebook”** to **“I’ve shipped a new metric/page into this dashboard with tests, docs, and CI all green.”** It is written for a Python/data‑science developer who is comfortable in notebooks and wants a repeatable way to land changes in this codebase.

The examples below use “add a new metric and page” as the running story, but the same steps apply if you are refining an existing analysis or wiring in a new survey wave.

---

### 1. Starting point: CSV + notebook

Assume you have:

- a CSV (or export from a survey tool)
- a Jupyter notebook where you:
  - load data with `pandas.read_csv`
  - clean a few columns
  - build counts / percentages
  - draw a couple of charts

Before changing this repo:

- **Clarify the user question** – what policy or operational question are you answering?
- **Decide the shape of the output** – a headline KPI, a chart, a table, or a narrative?
-, For the rest of this guide we will talk about a single new **metric** (e.g. “share of organisations that have formal volunteer supervision”) shown both:
  - as part of an existing page (e.g. Workforce & Operations), and
  - optionally, on a new page.

---

### 2. Move the core analysis into `src/eda.py`

Your notebook code usually mixes three concerns:

- **I/O**: reading files, fetching URLs.
- **Cleaning**: normalising strings, coercing numbers, handling missing values.
- **Analysis**: computing metrics from a cleaned DataFrame.

In this repo those concerns are split:

- `src/data_loader.py` handles **loading and cleaning**.
- `src/eda.py` holds **reusable analytical helpers**.
- `src/section_pages/` contains **page‑level rendering**, which calls into `eda` helpers.

To “productionise” notebook logic:

1. **Identify the 1–2 core metrics** your notebook cares about.
2. **Copy only the pure-analysis part** into a new helper in `src/eda.py`.
3. **Take a cleaned DataFrame as input** and return a plain `dict[str, Any]` with:
   - counts and percentages,
   - any small helper DataFrames you want to reuse across pages.

For example (sketch only):

```python
def volunteer_supervision_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Summarise whether organisations offer formal supervision for volunteers."""
    working = df.copy()
    n = len(working)
    has_supervision = (working["vol_supervision"] == "Yes").sum()
    pct_has_supervision = round(100 * has_supervision / n, 1) if n else 0.0

    return {
        "n": n,
        "n_has_supervision": int(has_supervision),
        "pct_has_supervision": pct_has_supervision,
    }
```

Keep this function:

- **Pure** – no Streamlit imports, no global state, no file I/O.
- **Typed** – give parameters and return value type hints.
- **Documented** – short docstring with `Args` / `Returns` where useful, mirroring existing helpers.

Run the unit tests that touch `src/eda.py` (see §5 below) to make sure you have not regressed existing behaviour.

---

### 3. Wire the metric into a section page

Once your helper lives in `src/eda.py`, the next step is to **surface it in the UI**.

The usual pattern:

1. Pick the right page under `src/section_pages/` (e.g. `workforce_and_operations.py`).
2. Import your new helper from `src.eda`.
3. Call it using the **filtered** `df` passed in from `src/app.py`.
4. Render results using the `src.charts` helpers or Streamlit primitives.

For example (pseudo‑diff only):

```python
from src.eda import workforce_operations, volunteer_supervision_summary


def render_workforce_and_operations(df: pd.DataFrame, n: int) -> None:
    ui_config = get_app_ui_config()
    if ui_config.suppressed:
        st.warning("Results suppressed due to small sample size.")
        st.stop()

    wf = workforce_operations(df)
    sup = volunteer_supervision_summary(df)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Organisations with volunteers", f"{wf['has_volunteers_pct']}%")
    with col2:
        st.metric("Offer formal supervision", f"{sup['pct_has_supervision']}%")
```

Key points:

- **Always respect k‑anonymity**: if the page already checks `ui_config.suppressed`, keep that guard so small filtered samples do not leak information.
- **Use the shared palettes and typography** from `src.config` and `src.charts` rather than hand‑coding Plotly options.
- **Keep layout simple and consistent** with existing cards and tables.

If you need a completely new page:

1. Create `src/section_pages/your_new_page.py` with a `render_*` function.
2. Add a `NavItem` into `src/navigation.py`.
3. Wire the page id into the dispatch block in `src/app.py` (mirroring the existing pattern).

---

### 4. Keep demo mode and tests happy

This repo is designed to **run safely without private data**, using:

- a bundled sample fixture (`tests/fixtures/wcva_sample_dataset.csv`), and
- runtime data‑source resolution in `src.config.resolve_dataset_source()`.

When you add new metrics:

- **Prefer columns that already exist** in both the real Wave dataset and the sample fixture.
- If you need a **new column**:
  - update the private Wave data source and the sample fixture;
  - extend `tests/fixtures/wcva_sample_dataset.csv` in a way that keeps existing regression tests stable (e.g. proportion‑preserving duplicates rather than changing headline percentages);
  - document the new column in `src/config.COLUMN_LABELS` if it is part of the questionnaire.
- For cross‑wave work, check `src/wave_context.py` and the Trends & Waves page:
  - use `build_wave_context_from_df` and `TREND_METRICS` as the extension points;
  - ensure that any new metrics are either robust to missing waves or clearly documented as Wave‑specific.

You should be able to:

- run the app in **demo mode** (no private dataset configured) and still see meaningful values for your new metric; and
- run `pytest` locally without the private dataset present.

If a test needs the real Wave data, make that explicit in the test with a clear skip condition and message.

---

### 5. Add or extend tests

Productionising notebook work is as much about **tests** as it is about code placement.

In this repo:

- small pure helpers live in `tests/unit/` (e.g. `test_eda_core.py`, `test_data_loader.py`);
- cross‑module behaviour lives in `tests/integration/`;
- end‑to‑end smoke tests live in `tests/e2e/`.

When you add a new metric:

1. **Unit test the helper** in `tests/unit/test_eda_core.py` (or a nearby file):
   - create a small in‑memory DataFrame (mirroring the `tiny_df` fixture pattern);
   - assert that counts and percentages are correct and within \[0, 100\];
   - test at least one edge case (e.g. empty DataFrame or all‑missing column).
2. If the metric appears in a **high‑level summary** (Overview, Executive Summary):
   - consider extending `tests/unit/test_metrics_executive_overview.py` so the fixture regression covers your new story;
   - avoid hard‑coding too many absolute numbers; focus on structure and critical percentages.
3. If you connect it into **Trends & Waves**:
   - add a new entry into `TREND_METRICS` in `src/wave_context.py`;
   - add an integration test that asserts your metric appears in the trend table with sensible values.

Before committing, run:

```bash
pytest tests/ -m "not e2e"
pytest tests/e2e/test_streamlit_smoke.py  # optional local e2e smoke
```

CI will also run mypy, Black, and isort (see §7).

---

### 6. Respect k‑anonymity and filters

The dashboard enforces a **k‑anonymity threshold** via `K_ANON_THRESHOLD` in `src/config.py`:

- filters (organisation size, scope, local authority, activity, paid staff, concerns) narrow the DataFrame;
- the app counts the remaining rows and sets `ui_config.suppressed` when the count is below `K_ANON_THRESHOLD` (default: 5);
- many section pages bail out early with a “Results suppressed due to small sample size” warning.

When adding metrics:

- **Do not bypass suppression**; treat `ui_config.suppressed` as a hard guard for any chart or table that could expose respondents.
- **Design pages to degrade gracefully** – when suppressed, show a short explanatory message instead of partial charts.
- If you need to compute intermediate numbers (e.g. to support cross‑wave aggregates) from a small slice, make sure:
  - those numbers are never shown directly to the user; or
  - they are aggregated to a level that preserves anonymity and aligns with WCVA’s data policy.

This is especially important when you later add **new survey waves** or more granular slices.

---

### 7. Run pre‑commit and keep CI green

This repository treats formatting, tests, and typing as part of “production quality”.

Locally you can run:

```bash
black src/ tests/
isort src/ tests/
pytest tests/ -m "not e2e"
mypy src/ tests/
```

If you have `pre-commit` installed (see the README and `CONTRIBUTING.md`):

- `pre-commit run --all-files` will run:
  - Black
  - isort
  - the fast non‑e2e test subset
  - mypy (on `src/` and `tests/`)

CI (GitHub Actions) will repeat these checks for your branch, plus:

- an e2e Streamlit import smoke test;
- a security scan with `pip-audit`.

Treat a **green CI run** as the gate for merging production changes.

---

### 8. Document the change

For a small new metric or page:

- Update **`CHANGELOG.md`** under `[Unreleased]`:
  - briefly describe the new metric/page;
  - mention if it affects demo mode, cross‑wave trends, or k‑anonymity behaviour.
- If it affects user behaviour or deployment:
  - tweak the **README** “Features” or “Usage” section;
  - consider a short note in **`docs/LEARNING_AND_BACKLOG.md`** if it adds a new pattern or policy.
- Keep docstrings in `src/eda.py`, `src/section_pages/`, and `src/wave_context.py` aligned with the behaviour you just added.

For larger changes (new survey wave, new deployment path, or new data policy), consider:

- adding or updating an **ADR** in `docs/adr/`;
- writing a short “what changed and why” note in `docs/learning/` if it teaches a reusable pattern.

---

### 9. From “Wave 2 only” to multi‑wave

The `Trends & Waves` page and `src/wave_context.py` are the backbone for **multi‑wave analysis**:

- `WaveContext` defines a validated schema for one survey wave.
- `WAVE1_CONTEXT` holds the existing hand‑crafted Wave 1 payload.
- `build_wave_context_from_df` derives a Wave 2‑style context from a row‑level DataFrame.
- `build_wave_registry_from_current_data` and `get_wave_registry` combine Wave 1 (static) and Wave 2+ (derived) into a registry for trend tables and charts.

To add a new survey wave in a future release:

1. **Prepare the Wave CSV**:
   - align column names with `src.config.COLUMN_LABELS` where possible;
   - for changed or new questions, decide whether they:
     - can map into existing canonical metrics (e.g. same Likert scale, different label); or
     - must remain wave‑specific (documented in a new block).
2. **Extend `build_wave_registry_from_current_data`**:
   - for a second derived wave (e.g. Wave 3), call `build_wave_context_from_df` again, possibly with a filtered slice (`df[df["wave"] == 3]`) or a separate dataset;
   - add the new context to the `waves` dict with a clear label and `wave_number` ordering.
3. **Update `TREND_METRICS`** if the new wave supports additional stable indicators.
4. **Add integration tests** in `tests/integration/`:
   - assert that multi‑wave registries still round‑trip correctly;
   - confirm that new waves appear in the trend table and that percentage‑point deltas behave as expected.
5. **Document the step‑by‑step “add a new wave” process**:
   - a short subsection in `docs/LEARNING_AND_BACKLOG.md` (roadmap and policy‑alignment);
   - a concrete example in this guide, once a second real wave is in production.

For future waves where question sets diverge more strongly (different columns, added qualitative questions), the plan is to introduce a small **mapping layer**:

- per‑wave config that maps raw columns → canonical metrics for trends;
- safe fallbacks when a metric is missing in a given wave;
- explicit documentation of which metrics can be compared across which waves.

That mapping layer is intentionally not over‑engineered yet, but it is tracked in the backlog so that future work on Wave 3+ can extend this repo in an enterprise‑ready way.

---

### 10. Putting it all together

When you next move work from a notebook into this repo, treat this as your checklist:

1. **Clarify the question** and output shape.
2. **Lift pure analysis** into a helper in `src/eda.py`.
3. **Wire the helper** into an existing or new `src/section_pages/` page.
4. **Respect demo mode and k‑anonymity**; keep the app usable without private data.
5. **Add tests** (unit + integration where appropriate).
6. **Run Black, isort, pytest, mypy** (or pre‑commit) locally.
7. **Update docs and changelog**.
8. **Open a PR** with a short description that links code, tests, and docs.

Following this loop turns one‑off exploratory analysis into repeatable, reviewable, and production‑ready features in the Baromedr Cymru dashboard.
