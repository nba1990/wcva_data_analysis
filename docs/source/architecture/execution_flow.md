---
title: Execution flow
---

# Execution flow

```{mermaid}
flowchart TD
  start["App start (streamlit run src/app.py)"] --> configure["Configure page (title, layout)"]
  configure --> resolveData["Resolve runtime dataset source"]
  resolveData --> loadData["load_dataset() in src/data_loader.py"]
  loadData --> cacheData["Cache with st.cache_data (shared across sessions)"]

  cacheData --> buildSidebar["Build sidebar filters & UI (app.py)"]
  buildSidebar --> navSidebar["Render sidebar navigation (navigation.render_sidebar_nav)"]
  navSidebar --> choosePage["Determine current page id"]

  choosePage --> dispatchPage["Dispatch to matching render_* in src/section_pages/*"]
  dispatchPage --> runAnalysis["Run analysis helpers (src/eda.py, src/wave_context.py)"]
  runAnalysis --> buildCharts["Build charts & KPIs (src/charts.py, src/sroi_charts/sroi_figures.py)"]
  buildCharts --> applyAccessibility["Apply accessibility config (text scale, palettes)"]
  applyAccessibility --> renderUI["Render UI in Streamlit"]
  renderUI --> rerun["User interaction triggers Streamlit reruns with updated session_state"]
  rerun --> buildSidebar
```

Key points (click through to the code):

- Streamlit drives the rerun loop; :mod:`src.app` is written so that each rerun is **idempotent** and uses ``st.session_state`` for per-session configuration.
- Data loading is performed once per process via :func:`src.data_loader.load_dataset`, cached with ``st.cache_data``, but filters and navigation are recomputed on each rerun.
- The sidebar and navigation are built via :func:`src.navigation.render_sidebar_nav` and the :class:`src.navigation.NavItem` model.
- Section pages follow a consistent pattern: take filtered data and configuration, call helpers from :mod:`src.eda` / :mod:`src.wave_context`, then build charts/tables using :mod:`src.charts` and :mod:`src.sroi_charts.sroi_figures`.

For a structural view of which modules import which, see :doc:`module_dependencies`. For the sidebar/page mapping itself, see :doc:`streamlit_pages`. For the underlying function and class APIs, see :doc:`api/index`.
