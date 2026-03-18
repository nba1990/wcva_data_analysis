<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Streamlit & modern data dashboards (quick reference)

*Last verified against version 0.2.3.*

This note distils ideas from `scratch/streamlit_python_chat_transcript.md` into a concise reference for future dashboard work.

## 1. Mental model for the stack

At a high level:

```text
User
  ↓
Streamlit app UI
  ↓
Python application logic
  ↓
Data layer (DuckDB / Pandas / Polars)
  ↓
Visualisation layer (Plotly / Altair / PyDeck)
  ↓
Rendered charts/tables/maps back in Streamlit
```

- **Python** is the language and glue.
- **Streamlit** is the web UI / interaction layer.
- **DuckDB / Pandas / Polars** handle tabular data and queries.
- **Plotly / Altair / PyDeck** render charts and maps which Streamlit embeds.

This matches how `src/app.py`, `src/eda.py`, `src/charts.py` and `src/wave_context.py` are structured today.

## 2. Libraries and when to use them

- **Pandas** – primary tabular engine for this project; good default for:
  - reading CSV/Excel,
  - joins and group-bys on medium-sized datasets,
  - feeding DataFrames into Plotly/Altair and WaveContext builders.

- **DuckDB** – future option when:
  - datasets grow large or many Parquet/CSV files need to be queried together;
  - you want SQL-style analytics (grouped aggregations, window functions) against local files.
  - Could sit behind EDA helpers (`src/eda.py`) while keeping the public interface unchanged.

- **Polars** – alternative columnar DataFrame engine:
  - offers faster/grouped operations and lazy evaluation;
  - useful for heavy ETL-style transforms if WCVA datasets become much larger.

- **Plotly** – main charting library already used in `src/charts.py`:
  - interactive dashboards (hover, zoom, legend toggles),
  - good for bar charts, time series, heatmaps, and SROI visuals,
  - integrates cleanly with `st.plotly_chart`.

- **Altair** – declarative charts:
  - well-suited for quick EDA views and small multiples,
  - pairs nicely with tidy DataFrames; can be used where “grammar of graphics” is clearer than imperative Plotly code.

- **PyDeck** – geospatial visualisation:
  - agenda item for any future **LA/regional maps** (e.g. mapping representation index by local authority),
  - integrates with `st.pydeck_chart`.

- **YData Profiling / PyGWalker** – rapid EDA tooling:
  - could power an internal-only “EDA playground” page for exploring new waves or datasets without writing custom charts.

## 3. Patterns worth reusing in this repo

From the transcript and current codebase, a few patterns are particularly valuable:

- **Section page composition**:
  - Keep heavy analysis in `src/eda.py` and `src/wave_context.py`.
  - Keep chart primitives in `src/charts.py` / `src.sroi_charts.sroi_figures`.
  - Let `src/section_pages/*` focus on narrative, layout, and chart composition.

- **Filters + derived metrics**:
  - Sidebar → filters (`src/app.py` and `src/filters.py`),
  - Derived columns in `src/data_loader.py`,
  - Aggregates in `src/eda.py`,
  - Charts in `src/charts.py`,
  - Qualitative narrative in `src.narratives` and `src.section_pages/*`.

- **Geospatial extensions (future)**:
  - Use LA codes/regions already in the dataset with PyDeck to build:
    - “sample representation by LA” maps,
    - potential retrofit or volunteering “cold spots” views.

- **Explainability/diagnostics (future)**:
  - If models are introduced (e.g. for risk scoring), libraries such as SHAP can be embedded via Streamlit for transparency.

For concrete project ideas aligned with WCVA and your wider work (retrofit, fuel poverty, community energy), see the “Technology exploration” and “Future dashboards” sections of `docs/LEARNING_AND_BACKLOG.md`.
