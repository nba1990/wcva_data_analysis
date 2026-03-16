<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Repo Tour for Python / Data-Science Developers

This project is a good example of the step from "Python analysis code" to
"maintained application code".

## Mental model

- `src/app.py`: the Streamlit entry point and orchestration layer
- `src/section_pages/`: page-level UI/rendering logic
- `src/data_loader.py`: dataset loading, cleaning, runtime source resolution
- `src/eda.py`: reusable analytical helpers
- `src/charts.py` and `src/sroi_charts/`: reusable figure factories
- `tests/`: regression, integration, and smoke checks
- `docs/`, `ARCHITECTURE.md`, `README.md`, `docs/adr/`: the operational memory of the project

## What changes compared with notebook-style work

- The app reruns top-to-bottom on interaction, so shared state must be explicit.
- Data loading needs deterministic resolution rules and good failure messages.
- Charts and metrics become reusable interfaces, not one-off snippets.
- Tests protect expected behaviour when you refactor.
- Documentation needs to explain both "what this code does" and "how to work on it safely".

## How to read this codebase

1. Start in `README.md` for run/deploy basics.
2. Read `ARCHITECTURE.md` to understand app flow and module boundaries.
3. Inspect `src/app.py` to see the orchestration path.
4. Follow one page into `src/section_pages/` and back into `src/eda.py`.
5. Read the relevant unit tests to see what behaviour is treated as stable.

## Full-stack concepts you can learn here without overclaiming

This repo is not a traditional REST backend + SPA frontend stack, but it still
teaches core product-engineering ideas:

- runtime configuration
- deployment environments
- secrets handling
- public vs private assets
- smoke tests and CI
- release tagging
- changelogs and ADRs
- safe git history rewrites for sensitive data mistakes
