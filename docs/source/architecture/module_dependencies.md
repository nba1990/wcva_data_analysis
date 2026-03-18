---
title: Module dependencies
---

# Module dependencies

This page surfaces **code-derived graphs** that show how top-level modules under `src/` depend on each other.

In this project, these diagrams are generated automatically by a script (see `scripts/generate_diagrams.py`) using `pydeps` and `pyreverse`, and written into `docs/source/architecture/auto/`.

```{note}
The diagrams below are examples; when you run the generation script locally or on Read the Docs, they will be refreshed from the current codebase.
```

## High-level packages (src/*)

```{graphviz} auto/packages.dot
```

This diagram comes from ``pyreverse`` and shows how the main packages relate to each other. For deeper, per-class detail you can also inspect ``auto/classes.dot``.

## Navigation and section pages

```{graphviz} auto/packages_nav_pages.dot
```

This focused view shows **only** the navigation layer and Streamlit section pages:

- ``src.navigation`` (see :mod:`src.navigation`) defines :class:`src.navigation.NavItem` and the sidebar model.
- ``src.section_pages.*`` (see :mod:`src.section_pages`) contains one render function per page that the app dispatches to.

Use this diagram alongside the :doc:`streamlit_pages` overview to understand how pages are wired together.

## Analysis and data-loading layer

```{graphviz} auto/packages_analysis_layer.dot
```

This graph highlights the **core analysis pipeline**:

- ``src.data_loader`` (see :mod:`src.data_loader`) resolves and loads the WCVA dataset and LA context.
- ``src.eda`` (see :mod:`src.eda`) provides reusable analysis helpers used by multiple pages.
- ``src.wave_context`` (see :mod:`src.wave_context`) models survey waves and trend context.

Together, these modules transform raw CSV data into analysis-ready structures used throughout the app.

## Charts and SROI figures

```{graphviz} auto/packages_charts_layer.dot
```

This graph focuses on the **visualisation layer**:

- ``src.charts`` (see :mod:`src.charts`) holds general-purpose chart and KPI builders.
- ``src.sroi_charts.sroi_figures`` (see :mod:`src.sroi_charts.sroi_figures`) concentrates SROI-specific figures and helpers.

These modules take processed data from ``src.eda`` / ``src.wave_context`` and turn it into Streamlit-friendly visuals.
