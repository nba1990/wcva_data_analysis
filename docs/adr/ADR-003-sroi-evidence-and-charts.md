<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# ADR-003 – SROI evidence integration and chart separation

## Context

The WCVA project needed to integrate **Social Return on Investment (SROI)** evidence for the Welsh voluntary sector in two distinct ways:

- As part of a **Streamlit dashboard page** (“SROI & References”), where users can interactively explore charts, references, and methodological caveats.
- As part of an **offline artefact pipeline**, generating PNG/SVG charts and documents under `references/SROI_Wales_Voluntary_Sector/` for reports and slide decks.

Early prototypes embedded SROI chart logic directly inside the offline script and/or Streamlit pages, which made the visuals:

- Harder to test.
- Prone to divergence between the dashboard and offline outputs.
- Difficult to extend with accessibility features like palette switches and text scaling.

## Decision

We created a dedicated SROI visualisation module, `src/sroi_charts/sroi_figures.py`, which:

- Exposes pure Plotly factories, all named `make_*_figure`, for:
  - Funding flows into the Welsh voluntary sector.
  - SROI ratio comparisons across key Wales-based studies.
  - The economic value of volunteering and unpaid care.
  - The measurement gap.
  - WCVA–WG funding and NLCF Wales grants.
  - Alignment heatmap between New Approach enablers and objectives.
  - A Plotly implementation of the New Approach framework flow.
  - The implementation timeline.
- Accepts `palette_mode` (`"brand"` / `"accessible"`) and `text_scale` arguments, applying them consistently to:
  - Colour choice via `BRAND_SEQUENCE` / `ACCESSIBLE_SEQUENCE`.
  - Base and title font sizes via a shared `_scale_layout` helper.
- Is used by:
  - `src/section_pages/sroi_references.py` for the interactive dashboard page.
  - `references/SROI_Wales_Voluntary_Sector/scripts/sroi_wales_voluntary_sector.py` for batch chart generation via a `save_plotly_figure` helper.

## Consequences

- All SROI visuals now share a single source of truth:
  - Any change to data points, titles, or labelling in `sroi_figures.py` automatically affects both the dashboard and offline exports.
  - Accessibility improvements (palette and text scaling) propagate everywhere those figures are used.
- Tests in `tests/unit/test_sroi_figures.py` enforce that:
  - Each `make_*` factory returns a `go.Figure` with a non-empty title.
  - Changing `palette_mode` changes colours.
  - Increasing `text_scale` increases font sizes in the layout.
- The Mermaid-based framework flow diagram was replaced by a Plotly-based implementation for SVG outputs (while retaining a Mermaid PNG flow where helpful), avoiding brittle SVG post-processing and ensuring consistent text rendering across viewers. This decision slightly increases the amount of plotting code but substantially improves robustness and testability.***
