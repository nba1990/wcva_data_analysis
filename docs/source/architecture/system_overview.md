---
title: System overview
---

# System overview

```{mermaid}
flowchart TD
  user["User in browser"] --> streamlitServer["Streamlit server (src/app.py)"]
  streamlitServer --> sidebar["Sidebar filters & navigation"]
  sidebar --> navigationModule["Navigation module (src/navigation.py)"]
  navigationModule --> sectionPages["Section pages (src/section_pages/*)"]

  streamlitServer --> dataLoader["Data loader (src/data_loader.py)"]
  dataLoader --> wcvaCsv["WCVA survey dataset (CSV)"]
  dataLoader --> laContext["LA context CSV (references/context)"]

  sectionPages --> eda["Analysis helpers (src/eda.py)"]
  sectionPages --> waveContext["Wave registry & context (src/wave_context.py)"]
  sectionPages --> charts["Charts & UI (src/charts.py, src/sroi_charts/sroi_figures.py)"]

  charts --> visuals["Interactive charts, tables, KPIs"]
  visuals --> user
```

At a glance:

- The **entry point** is :mod:`src.app`, which configures Streamlit, loads data, and dispatches to section pages.
- **Navigation** is centralised in :mod:`src.navigation`, which defines the sidebar menu and current page via :class:`src.navigation.NavItem`.
- Each **section page** in :mod:`src.section_pages` pulls together filtered data, reusable analysis from :mod:`src.eda` and :mod:`src.wave_context`, and branded charts from :mod:`src.charts` / :mod:`src.sroi_charts.sroi_figures`.
- Runtime data comes from WCVA survey CSVs and LA context CSVs (see :mod:`src.data_loader`); a bundled sample dataset is used for demo/docs builds.

If you want to see how this high-level picture maps to imports, continue to :doc:`module_dependencies`. For detailed Python APIs grouped by layer, see :doc:`api/index`.
