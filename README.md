<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# WCVA Baromedr Cymru – Wave 2 Dashboard

[![CI](https://github.com/nba1990/wcva_data_analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/nba1990/wcva_data_analysis/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://github.com/nba1990/wcva_data_analysis)
[![Issues](https://img.shields.io/github/issues/nba1990/wcva_data_analysis.svg)](https://github.com/nba1990/wcva_data_analysis/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/nba1990/wcva_data_analysis.svg)](https://github.com/nba1990/wcva_data_analysis/pulls)
[![Release](https://img.shields.io/github/v/release/nba1990/wcva_data_analysis.svg)](https://github.com/nba1990/wcva_data_analysis/releases)
[![Live demo](https://img.shields.io/badge/Streamlit-live%20demo-brightgreen.svg)](https://baromedr.streamlit.app/)
[![Docs](https://readthedocs.org/projects/baromedr/badge/?version=latest)](https://baromedr.readthedocs.io/en/latest/)

Current release: **0.2.3**

This repository contains an interactive **Streamlit** dashboard and supporting scripts for analysing **Baromedr Cymru Wave 2** – a quarterly temperature check of the Welsh voluntary sector – with a particular focus on volunteering, workforce, finances, and SROI evidence for the Welsh voluntary sector.

The dashboard is designed to:

- Provide an accessible, WCVA‑branded interface for exploring Wave 2 findings.
- Support policy and analytical discussions about demand, capacity, and volunteering.
- Integrate SROI/Wales reference material and charts alongside the main survey data.

For a deeper architectural description, see `ARCHITECTURE.md`. For a short **developer tour** (how to read tests and docs) and **future dashboards/backlog**, see the end of `ARCHITECTURE.md` and `docs/LEARNING_AND_BACKLOG.md`. Policy-focused questions for WCVA teams are in `plans/policy_questions.md`.

**New here? Picking this up again?**
(1) This README: what the project is, how to install and run.
(2) **`ARCHITECTURE.md`**: how the code is structured (app → data → charts → section pages).
(3) **`CONTRIBUTING.md`**: dev setup, tests, formatting, and doc/typing standards (§7).
(4) **`docs/LEARNING_AND_BACKLOG.md`**: backlog, testing strategy, coverage, safe/unsafe patterns.
(5) **`docs/learning/`**: curated "Python/data-science to app/deploy/git" guides grounded in this codebase.
(6) **Sphinx docs** (see § Documentation below): single place for getting started, architecture, API reference. Live docs: `https://baromedr.readthedocs.io/en/latest/` – includes an operator-facing :doc:`deployment checklist <deployment_checklist>` when viewed on Read the Docs.

---

## Features

- **Interactive multi-page Streamlit dashboard**:
  - Overview
  - Volunteer Recruitment
  - Volunteer Retention
  - Workforce & Operations
  - Demographics & Types
  - Earned Settlement
  - Trends & Waves
  - Executive Summary
  - At-a-Glance (infographic)
  - Deployment Health
  - Data Notes
  - **SROI & References** (evidence base and mind-map)
- **WCVA branding and accessibility**:
  - Brand and colour‑blind‑friendly palettes.
  - Text scaling for charts and layout.
  - Alt‑text metadata for charts and clear labelling.
- **k-anonymity suppression**:
  - Results are suppressed when filtered sample size falls below a threshold (default: 5 organisations).
- **Offline SROI artefacts**:
  - Batch script to generate PNG/SVG charts and supporting metadata for SROI/Wales documentation under `references/SROI_Wales_Voluntary_Sector/`.

---

## Project Structure

```text
<project-root>/
│
├── scripts/
│   ├── generate_diagrams.py      # Refresh Graphviz/Mermaid-derived documentation diagrams
│   └── run_quality_checks.sh     # One-shot local quality runner (quick or full)
│
├── src/
│   ├── __init__.py
│   ├── app.py                    # Streamlit multi-page app: filters, nav, page dispatch
│   ├── config.py                 # WCVA palettes, response orderings, k-anonymity, chart defaults
│   ├── data_loader.py            # Data loading, cleaning, derived columns
│   ├── eda.py                    # Analytical helpers (demand, workforce, recruitment, profiles, etc.)
│   ├── charts.py                 # WCVA-branded generic Plotly chart helpers + show_chart wrapper
│   ├── sroi_charts/
│   │   └── sroi_figures.py       # SROI/Wales-specific Plotly figure factories
│   ├── section_pages/            # Per-page renderers (render_overview, render_trends_and_waves, etc.)
│   │   └── deployment_health.py  # Runtime/deployment checks for required assets
│   ├── navigation.py             # NavItem definitions + sidebar navigation rendering
│   ├── narratives.py             # Narrative text helpers for executive summaries
│   ├── wave_context.py           # Cross-wave registry and trend helpers (built from per-wave schemas)
│   ├── wave_schema.py            # Loader + evaluators for per-wave schemas in config/waves/
│   └── generate_presentation.py  # Slide deck / PDF generation (optional)
│
├── references/
│   ├── context/                 # Public local-authority context CSV used by profile/geography views
│   └── SROI_Wales_Voluntary_Sector/
│       ├── docs/                 # SROI briefing, mind-map HTML/Markdown, PDF exports
│       ├── output/               # Generated SROI charts (PNG/SVG) and meta JSON
│       └── scripts/
│           └── sroi_wales_voluntary_sector.py  # Batch chart generator using sroi_figures
│
├── tests/
│   ├── unit/                     # Unit tests for config, charts, EDA, navigation, SROI figures, etc.
│   ├── integration/              # Integration tests across infographic, wave context, trends
│   ├── e2e/                      # End-to-end smoke tests for the Streamlit app
│   └── fixtures/                 # Small sample datasets for regression tests
│
├── docs/
│   ├── source/                   # Sphinx source (index, getting_started, architecture, api/)
│   ├── Makefile                  # make html to build Sphinx docs
│   ├── requirements-docs.txt     # Sphinx and theme (install after requirements.txt)
│   ├── adr/                      # Architecture Decision Records (ADR-001 … ADR-008)
│   ├── learning/                 # Curated learning guides anchored to this repo
│   ├── DOCKER_AND_DEPLOYMENT.md  # Docker build/run and self-hosting guide
│   └── LEARNING_AND_BACKLOG.md   # Backlog, testing strategy, coverage
│
├── output/                       # Presentation outputs (HTML/PDF) if generated
├── .streamlit/
│   └── config.toml               # WCVA-branded Streamlit theme
├── scratch/                      # Ignored temporary notes, transcripts, and drafts
├── ARCHITECTURE.md               # High-level architecture and flow
├── CHANGELOG.md                  # Version history and notable changes
├── CONTRIBUTING.md               # How to contribute (setup, tests, PRs)
├── Dockerfile                    # Container image for the dashboard
├── docker-compose.yml            # Compose stack for local or server deployment
├── .pre-commit-config.yaml       # Optional pre-commit hooks (Ruff, mypy, pytest, import-linter)
├── pyproject.toml                # Ruff, mypy, coverage, packaging config; project metadata
├── pytest.ini                    # Pytest discovery and markers (e.g. e2e)
├── requirements.txt
├── requirements-dev.txt          # Dev / CI tooling (Ruff, mypy, pytest, security, build)
├── README.md
└── LICENSE
```

---

## Installation

```bash
git clone <repository-url>
cd wcva_data_analysis  # or your chosen directory name

# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install runtime dependencies
pip install -r requirements.txt

# Install development and CI tooling
pip install -r requirements-dev.txt
```

**Tested with** Python 3.11 and 3.12. The project uses lower-bound version constraints in `requirements.txt`; for reproducible installs you can pin versions (e.g. `pip freeze > requirements-lock.txt`) or use the same minor Python version as CI.

### Pre-commit (optional)

To run Ruff, type checking, architecture checks, and tests automatically before each commit:

```bash
pip install pre-commit
pre-commit install
```

Then `git commit` will run the hooks. See **`CONTRIBUTING.md`** for more.

### One-shot local quality checks

If you want one command that runs the main local quality gates, use:

```bash
scripts/run_quality_checks.sh
```

That runs the broader local suite: Ruff, import-linter, mypy, non-e2e tests with coverage, the e2e smoke test, security scans, package build, diagram generation, and the Sphinx docs build.
`pip-audit` in that full pass needs outbound network access to query vulnerability data.

For a faster day-to-day pass while you are iterating on code, use:

```bash
scripts/run_quality_checks.sh --quick
```

### Docker (optional)

To run the dashboard in a container without installing Python locally:

```bash
docker compose up -d
# Or: docker build -t wcva-baromedr-dashboard . && docker run -p 8501:8501 wcva-baromedr-dashboard
```

Then open **http://localhost:8501**. For full Docker and self-hosting instructions (data mounts, reverse proxy, env vars), see **`docs/DOCKER_AND_DEPLOYMENT.md`**.

---

## Usage

### Interactive Dashboard

```bash
streamlit run src/app.py
```

Opens in your browser at `http://localhost:8501`. Use the sidebar to:

- Navigate between pages.
- Filter by organisation size, geographic scope, local authority, main activity, and concerns.
- Toggle colour‑blind‑friendly mode.
- Adjust chart text size.
- Download chart data where available.

If the private dataset is not configured, the app boots in explicit **demo mode** using the bundled sample fixture. Check the **Deployment Health** page to see which runtime source was resolved.

### Generate Executive Presentation (optional)

```bash
python -m src.generate_presentation
```

Produces two files in `output/`:

- `presentation.html` — self-contained reveal.js slide deck (emailable, opens in any browser).
- `presentation.pdf` — structured PDF with table of contents and bookmarks.

In demo mode, the default behavior is to write `presentation_demo.html` and `presentation_demo.pdf` with prominent sample-data labelling.

### Generate SROI Charts (optional)

```bash
python references/SROI_Wales_Voluntary_Sector/scripts/sroi_wales_voluntary_sector.py
```

Regenerates SROI PNG/SVG charts and JSON sidecar metadata in `references/SROI_Wales_Voluntary_Sector/output/`.

---

## Documentation (Sphinx)

Built documentation helps new users and developers get oriented. It includes a **getting started** guide, **architecture** overview, **contributing** summary, and full **API reference** generated from the codebase.

**Live docs**: https://baromedr.readthedocs.io/en/latest/

**Build the docs** (requires project dependencies and Sphinx):

```bash
pip install -r requirements.txt
pip install -r docs/requirements-docs.txt
cd docs && make html
```

Then open `docs/build/html/index.html` in a browser. On Windows use `docs\make.bat html` instead of `make html`.

**Note:** When building, Sphinx imports the app and Streamlit may print warnings (e.g. "No runtime found", "missing ScriptRunContext"). These are expected when the app is loaded outside `streamlit run` and can be ignored; the HTML docs are still generated correctly.

This repository also includes a minimal [Read the Docs](https://readthedocs.org/) configuration in `.readthedocs.yaml`, and the public docs are hosted at https://baromedr.readthedocs.io/en/latest/

### Documentation index

| Document | Purpose |
|----------|---------|
| **README.md** (this file) | Overview, install, run, config, testing, deployment, orientation. |
| **ARCHITECTURE.md** | High-level flow, modules, session state, performance, how to extend, developer tour, future dashboards. |
| **CONTRIBUTING.md** | Dev setup, tests, lint, Sphinx build, branching, PRs, doc/typing standards (§7). |
| **CHANGELOG.md** | Version history and notable changes. |
| **docs/LEARNING_AND_BACKLOG.md** | Backlog, testing strategy, coverage, fixture notes, safe/unsafe patterns, policy pointers. |
| **docs/learning/** | Curated learning guides for moving from Python/data-science work into app, deploy, testing, and git workflow using this repo. |
| **docs/DOCKER_AND_DEPLOYMENT.md** | Docker build/run, docker-compose, self-hosting, env vars, security, and a secrets/runtime configuration checklist. |
| **docs/HISTORY_REWRITE_AND_STREAMLIT_SECRETS.md** | Runbook for purging `datasets/` from Git history and configuring private runtime data on Streamlit Community Cloud. |
| **docs/adr/** (ADR-001 … ADR-008) | Decisions: Streamlit UI, navigation, SROI charts, state/caching, Docker, CI/testing, runtime data/demo mode, and the multi-wave schema/mapping layer. |
| **Sphinx / Read the Docs** (`docs/source/`, build: `docs/build/html/`) | Getting started, architecture, contributing, operations runbook, privacy/suppression explainer, full API reference. Live site: `https://baromedr.readthedocs.io/en/latest/`. |
| **docs/source/release_process.md** | Canonical release runbook: verification checklist, tagging, and publishing steps. |
| **docs/source/capability_clusters.md** | General-purpose capability-cluster map (PaaS/SaaS/product engineering), linked back to this repo’s concrete practices. |
| **docs/source/improvements_review.md** | Capability-cluster audit + prioritised improvement backlog for this codebase. |
| **pytest.ini** | Test discovery, `e2e` marker. |
| **pyproject.toml** | Ruff, mypy, coverage, and packaging config. |

---

## Configuration

All core configuration is centralised in `src/config.py`:

- **WCVA brand palette** and colour‑blind‑safe alternative sequences.
- **Column-to-question mappings** from the Baromedr questionnaire.
- **Response orderings** for consistent chart axes.
- **Chart defaults** (font, sizing, backgrounds).
- **k-anonymity threshold** (`K_ANON_THRESHOLD`, default: 5) used for suppression logic.
- **Wave context** mapping for cross-wave comparisons.
- **Debug flags** (environment variables): set `WCVA_DEBUG_MEMORY=1` (or `true`/`yes`) to show process memory usage in the sidebar when running the Streamlit app.
- **Output override** (environment variable): set `WCVA_OUTPUT_DIR` to write presentation outputs somewhere other than the repo-local `output/` folder.

The Streamlit theme is set in `.streamlit/config.toml`.

**Runtime data sources**: The private Wave 2 dataset is no longer tracked in Git. The app resolves it in this order:

- `WCVA_DATASET_PATH`
- `dataset_path` in Streamlit secrets
- `WCVA_DATASET_URL`
- `dataset_url` in Streamlit secrets
- local untracked fallback: `datasets/WCVA_W2_Anonymised_Dataset.csv`

The public local-authority context file now lives at `references/context/la_context_wales.csv`, with optional overrides via `WCVA_LA_CONTEXT_PATH`, `WCVA_LA_CONTEXT_URL`, or the matching Streamlit secret keys.

**Secrets**: Do not commit API keys, passwords, tokens, or private dataset URLs. Use environment variables or Streamlit’s [Secrets Manager](https://docs.streamlit.io/develop/concepts/connections/secrets-management) (see `.streamlit/secrets.example.toml`) for runtime configuration.

**Demo mode**: If the real Wave dataset is unavailable, the app and presentation generator fall back to the bundled sample fixture and mark the session/output as **DEMO / SAMPLE DATA**. This keeps docs builds, smoke tests, and first deployments working without pretending the fixture is a real Wave release.

---

## Testing

For the closest local equivalent to the project quality gates, run:

```bash
scripts/run_quality_checks.sh
```

For a faster developer pass, run:

```bash
scripts/run_quality_checks.sh --quick
```

You can still run individual commands directly when needed. For example, run the full test suite with:

```bash
pytest
```

To exclude end-to-end tests (e.g. in CI or when you don't have a Streamlit runtime):

```bash
pytest -m "not e2e"
```

**CI (GitHub Actions):** On every push and pull request, `.github/workflows/ci.yml` runs tests (Python 3.11 and 3.12), Ruff lint/format checks, import-linter contracts, mypy, dependency and code security scans, package build validation, docs build, and an e2e smoke test. The project uses pip-based requirements files rather than Conda. The local `scripts/run_quality_checks.sh` runner mirrors those quality gates in one place. See `pytest.ini` for test discovery and the `e2e` marker.

Highlights:

- `tests/test_wcva_metrics_wave2.py`:
  - Sanity-checks the main Wave 2 headline metrics against the QA log.
- `tests/unit/test_charts_core.py`:
  - Validates generic chart helpers, alt-text, and layout basics.
- `tests/unit/test_sroi_figures.py`:
  - Asserts that SROI chart factories return figures with titles and that `palette_mode` / `text_scale` behave as expected.
- `tests/unit/test_navigation.py`:
  - Ensures navigation IDs are unique and wired into `src/app.py`.
- `tests/unit/test_metrics_executive_overview.py`:
  - Uses a small fixture dataset (`tests/fixtures/wcva_sample_dataset.csv`) to assert that key Overview/Executive metrics and `executive_highlights()` behave as expected (regression guard). The fixture includes multi-select columns so executive summary highlights run without skipping.

A quick data-load smoke test:

```bash
python -c "from src.data_loader import load_dataset; df = load_dataset(); print(f'OK: {df.shape}')"
```

### Troubleshooting

- **"Results suppressed" in the dashboard** – The filtered sample has fewer than 5 organisations (k-anonymity). Widen or clear filters so more rows are included.
- **Sphinx build prints Streamlit warnings** – Expected when building docs; the app is imported outside `streamlit run`. Ignore them; the HTML output is correct.
- **Executive-overview or executive-highlights test skips / fails** – The fixture `tests/fixtures/wcva_sample_dataset.csv` must include multi-select columns (`concerns_1`, `concerns_2`, `actions_10`, etc.) so that `executive_highlights()` has data. See `docs/LEARNING_AND_BACKLOG.md` §3.2 and the fixture file.
- **Dataset not found** – Set `WCVA_DATASET_PATH` or `WCVA_DATASET_URL`, add `dataset_path` / `dataset_url` in Streamlit secrets, or place an untracked local copy at `datasets/WCVA_W2_Anonymised_Dataset.csv`.
- **App shows DEMO / SAMPLE DATA** – The private Wave dataset was not resolved, so the bundled fixture was used. Review the **Deployment Health** page and configure a real dataset path or URL.
- **Unsure which deployment file is missing** – Open the in-app **Deployment Health** page; it reports required and optional runtime files.

---

## Deployment Notes

### Docker and self-hosting

- **Docker**: use the included `Dockerfile` and `docker-compose.yml` to build and run the dashboard in a container. See **`docs/DOCKER_AND_DEPLOYMENT.md`** for:
  - Build and run commands (Compose and plain Docker).
  - Runtime data-source options, public reference assets, and optional volume mounts.
  - Self-hosting on a server with a reverse proxy (e.g. Nginx).
  - Environment variables (e.g. `WCVA_DEBUG_MEMORY`) and basic security notes.

### Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a new Streamlit app:
   - **Repository**: your GitHub repo.
   - **Main file**: `src/app.py`.
3. Ensure `requirements.txt` lists all required dependencies.

Considerations:

- Choose **Python 3.11 or 3.12** in the app's **Advanced settings**. Streamlit Community Cloud sets the Python version from the deploy UI, not from a repo file such as `runtime.txt`.
- Store the private dataset as a secret-backed **URL or runtime path**, not in the repo. See `.streamlit/secrets.example.toml` and `docs/HISTORY_REWRITE_AND_STREAMLIT_SECRETS.md`.
- Use the in-app **Deployment Health** page after startup to verify that required files and optional reference assets are present in the runtime environment.
- `st.cache_data` is used for dataset loading so all sessions share the same read‑only base DataFrame.
- Avoid unnecessary large in-memory artefacts; prefer computed summaries.

### Other environments

For local servers or containers:

- Install from `requirements.txt` and run `streamlit run src/app.py` behind a reverse proxy, or use the Docker image as described in `docs/DOCKER_AND_DEPLOYMENT.md`.

---

## SROI & References Page and Markmap Embedding

The SROI & References page (`src/section_pages/sroi_references.py`):

- Uses `src/sroi_charts/sroi_figures.py` factories to create interactive Plotly charts for:
  - Funding flows.
  - SROI ratio comparisons.
  - Economic value of volunteering and unpaid care.
  - Measurement gap.
  - WCVA–WG funding and NLCF Wales.
  - Alignment heatmap, framework flow, and implementation timeline.
- Passes per-session `palette_mode` and `text_scale` (from `get_app_ui_config()`) through to all SROI chart factories.
- Embeds a Markmap/Freeplane mind-map via:
  - Reading `references/SROI_Wales_Voluntary_Sector/docs/WCVA_Text_Interactive_MindMap.html`.
  - Rendering it with `st.components.v1.html(html, height=1920, scrolling=True)`.

To add another evidence‑style page, copy this pattern:

1. Add a new `render_*` function under `src/section_pages/`.
2. Add a matching `NavItem` to `src/navigation.py`.
3. Wire the page id into the dispatch block in `src/app.py`.

---

## Multi-user Behaviour

On Streamlit Community Cloud and similar deployments:

- Each browser tab gets its own **session**.
- Per-user UI state (filters, page, accessibility settings) lives in `st.session_state`, including the UI config dataclass accessed via `get_app_ui_config()`.
- Shared resources:
  - The main dataset is loaded via `st.cache_data`, whether it comes from a local file path or a secret-backed URL.

This means:

- One user’s filters or text size do **not** affect another user’s view.
- Expensive data loading is shared where appropriate, while interactive state remains session-specific.

See `ARCHITECTURE.md` and the ADRs in `docs/adr/` (e.g. ADR-004 for state/caching, ADR-005 for Docker, ADR-006 for CI and testing) for more detail.

---

## Backlog and learning

- **`docs/LEARNING_AND_BACKLOG.md`** – Backlog items (PyGWalker, DuckDB, PyDeck, future dashboards), testing strategy notes, and safe/unsafe patterns.
- **`docs/learning/`** – Curated guides on repo structure, private data/secrets, demo mode, deployment, testing, releases, and git hygiene using this repo as the example.
- **`docs/DOCKER_AND_DEPLOYMENT.md`** – Docker build/run, docker-compose, self-hosting, and deployment options.
- **`ARCHITECTURE.md`** – Sections 9–10: developer tour (how to read tests and docs) and future dashboards/backlog.
- **`plans/policy_questions.md`** – High-priority policy questions for WCVA teams; useful for Wave 3 design and briefings.

---

## Contributing

Guidelines for contributions:

1. Fork the repository and create a feature branch.
2. Install dependencies and (optionally) pre-commit (see above).
3. Add or update tests where appropriate; run `pytest` (or `pytest -m "not e2e"`).
4. Run `ruff check .` and `ruff format .` so CI passes.
5. Follow the project’s **documentation and typing standards**: module and function docstrings (with Args/Returns where useful), type hints on parameters and return values. See **`CONTRIBUTING.md`** §7.
6. Submit a pull request describing the change and motivation.

Full details: **`CONTRIBUTING.md`**.

---

## License and third-party notices

- **Project license**: GNU Affero General General Public License v3.0 (AGPL v3.0).
  Permissions of this strongest copyleft license are conditioned on making available complete source code of licensed works and modifications, which include larger works using a licensed work, under the same license. Copyright and license notices must be preserved. Contributors provide an express grant of patent rights. When a modified version is used to provide a service over a network, the complete source code of the modified version must be made available.
- **Third-party dependencies**: see `THIRD_PARTY_LICENSES.md` for a curated list of major libraries, tools, and their licenses.
- **License notices**: source and config files use comment-based AGPLv3 notices, while Markdown files use a hidden metadata block to keep rendered docs clean.
- **Idempotent re-application**: run `python tools/apply_license_headers.py` from the repo root to (re)apply the standard notices to tracked files.

---

## Maintainers

- Project maintainers can be reached via the repository issue tracker or pull requests.
