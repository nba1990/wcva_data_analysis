<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# ADR-006 – CI and testing approach

## Context

The project needs automated checks on every push and pull request so that:

- Tests run on supported Python versions and failures are caught before merge.
- Code style (formatting, import order) is consistent and enforced.
- Type checking and dependency security are part of the pipeline.
- End-to-end or UI-heavy tests can be run separately so that fast feedback (unit/integration) is the default.

The repository previously had workflows that did not match the actual setup (e.g. Conda-based or Pylint-based), leading to repeated CI failures and confusion. We wanted a single, clear pipeline that uses the same dependency and tooling stack as local development (pip, `requirements.txt`).

## Decision

We use a **single GitHub Actions workflow** (`.github/workflows/ci.yml`) with **pip** and **requirements.txt** (no Conda). The workflow defines separate jobs:

- **test** (matrix: Python 3.11, 3.12): Install deps, run `pytest tests/ -m "not e2e"` with coverage; upload coverage artifact. This excludes tests marked `@pytest.mark.e2e` so that the default CI run does not require a full Streamlit runtime or browser.
- **e2e-smoke**: Python 3.12 only; runs `pytest tests/e2e/test_streamlit_smoke.py` to verify the app module can be imported and basic wiring works. Kept minimal to avoid flakiness from UI automation.
- **lint**: Black and isort in check mode on `src/` and `tests/`. Configuration is in `pyproject.toml` (e.g. isort profile = black).
- **typecheck**: mypy on `src/` with config in `pyproject.toml`. Gradual typing is used (e.g. some strict checks disabled) so that existing code passes while new code can adopt stricter hints.
- **security**: pip-audit to report known vulnerabilities in dependencies.

Test discovery and markers are configured in **pytest.ini**: `e2e` marker is registered with a short description; `addopts = --strict-markers` so that unregistered markers cause a failure. This keeps the test suite self-documenting and prevents typos in markers.

We **do not** run Conda, Pylint, or legacy workflows; those were removed in favour of this single pipeline.

## Consequences

- Every push/PR gets consistent feedback: tests, format, types, and security in one place.
- Contributors use the same tools locally (Black, isort, pytest, mypy) as CI; CONTRIBUTING.md and README describe how to run them.
- E2e tests are opt-in in the default pytest run (`-m "not e2e"`), so local and CI unit/integration runs stay fast; e2e is run in a dedicated job.
- Coverage is produced as an artifact for optional inspection or future quality gates.
- New contributors and future maintainers have a single workflow to read and one place to add new steps (e.g. another lint tool) without navigating multiple legacy configs.
- Documentation (README, CONTRIBUTING, `docs/LEARNING_AND_BACKLOG.md`) references this workflow and the pytest marker so that the “why” is recorded alongside the code.
