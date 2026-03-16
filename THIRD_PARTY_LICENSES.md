<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Third-Party Licenses

It depends on a number of third-party libraries and tools, which are licensed under
their own terms as summarised below. This document is a best-effort overview and
does **not** replace the original license texts; always refer to the upstream
projects for authoritative terms.

## 1. Python runtime dependencies

These are declared in `requirements.txt` and are required to run the dashboard.

- **pandas**
  - Use: tabular data structures and analysis for the Wave 2 dataset.
  - License: BSD-3-Clause (pandas development team).
  - Home: https://pandas.pydata.org/

- **numpy**
  - Use: numerical arrays and vectorised operations underpinning pandas and some metrics.
  - License: BSD-3-Clause (NumPy developers).
  - Home: https://numpy.org/

- **plotly**
  - Use: interactive Plotly figures for all charts and SROI visualisations.
  - License: MIT License (Plotly, Inc.).
  - Home: https://plotly.com/python/

- **streamlit**
  - Use: web application framework for the interactive dashboard UI.
  - License: Apache License 2.0.
  - Home: https://streamlit.io/

- **kaleido**
  - Use: static image export of Plotly figures (PNG/SVG) for reports and SROI artefacts.
  - License: MIT License (Plotly, Inc.).
  - Home: https://github.com/plotly/Kaleido

- **fpdf2**
  - Use: generating PDF reports and presentations from dashboard outputs.
  - License: MIT License.
  - Home: https://github.com/PyFPDF/fpdf2

- **pydantic** / **pydantic-core**
  - Use: data models and validation for configuration and runtime data structures.
  - License: MIT License.
  - Home: https://docs.pydantic.dev/

- **psutil**
  - Use: optional memory usage reporting in the dashboard sidebar.
  - License: BSD-3-Clause.
  - Home: https://github.com/giampaolo/psutil

## 2. Python development and testing dependencies

Used only for development, formatting, linting, and tests.

- **black**
  - Use: opinionated Python code formatter.
  - License: MIT License.
  - Home: https://github.com/psf/black

- **isort**
  - Use: import sorting to keep Python imports consistent.
  - License: MIT License.
  - Home: https://pycqa.github.io/isort/

- **pytest**
  - Use: test runner for unit, integration, and end-to-end smoke tests.
  - License: MIT License.
  - Home: https://docs.pytest.org/

- **pytest-cov**
  - Use: test coverage reporting integration for pytest.
  - License: MIT License.
  - Home: https://github.com/pytest-dev/pytest-cov

## 3. Documentation stack

Dependencies declared in `docs/requirements-docs.txt` for Sphinx documentation builds.

- **Sphinx**
  - Use: documentation generator for the API and architecture docs under `docs/`.
  - License: BSD-3-Clause.
  - Home: https://www.sphinx-doc.org/

- **sphinx-rtd-theme**
  - Use: Read the Docs HTML theme for the Sphinx site.
  - License: MIT License.
  - Home: https://github.com/readthedocs/sphinx_rtd_theme

## 4. CI, security, and tooling

These tools are used in GitHub Actions or local development; they may be installed
transitively via configuration but are noted here for clarity.

- **mypy**
  - Use: optional static type checking configured in `pyproject.toml`.
  - License: MIT License.
  - Home: http://www.mypy-lang.org/

- **pip-audit**
  - Use: dependency vulnerability scanning in CI (`.github/workflows/ci.yml`).
  - License: Apache License 2.0.
  - Home: https://github.com/pypa/pip-audit

- **pre-commit** hooks (configured in `.pre-commit-config.yaml`)
  - Use: local git hooks for formatting, linting, and safety checks.
  - Each hook is licensed under its own upstream terms; see the hook repositories
    referenced in `.pre-commit-config.yaml` for details.

## 5. Frontend assets and references

The repository bundles reference documents and generated artefacts under
`references/SROI_Wales_Voluntary_Sector/`. These include Markdown, PDF, HTML,
PNG, and SVG files generated from upstream sources and internal analysis.

- SROI briefing documents, mind maps, and exported charts are derived from
  work commissioned for WCVA and are redistributed here under terms compatible
  with the main project license or with explicit permission from the rights
  holder.
- Where specific third-party assets (icons, fonts, or diagrams) have their own
  licenses, those are documented alongside the assets or in the upstream tools
  used to generate them.

## 6. Data and sample datasets

The repository includes sample datasets (e.g. `tests/fixtures/wcva_sample_dataset.csv`)
for testing and demonstration. These are anonymised and/or synthetic extracts
derived from WCVA Wave 2 data and are provided solely for testing and illustrative
purposes. They are **not** licensed for reuse as real-world survey data.

Private runtime datasets referenced by the application (e.g. anonymised Wave 2
CSV files mounted into `runtime-data/`) are **not** distributed in this
repository and remain subject to WCVA’s own data sharing agreements.

## 7. Notes and updates

- This file is maintained manually; when adding or removing dependencies, please
  update the relevant section and include the license name and a link to the
  upstream project.
- This summary is provided for convenience and does not constitute legal advice.
  If you have questions about license compatibility or obligations under AGPLv3,
  consult a qualified legal professional.
