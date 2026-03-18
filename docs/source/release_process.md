---
title: Release process
---

# Release process

This page is the **single source of truth** for how releases are prepared, verified, tagged, and published for this repository.

It is written to be usable both:

- for this Streamlit dashboard repo, and
- as a general lightweight release runbook for similar Python projects.

## Release principles (keep it lightweight)

- **Small, safe releases** beat large, risky ones.
- **Release notes are a product artefact** (they are how others learn what changed).
- **CI is the contract**: if CI is red, it is not releasable.

## Versioning policy

This repo uses lightweight semantic versioning:

- **MAJOR**: breaking change to runtime/deployment expectations.
- **MINOR**: new capability that remains backwards compatible.
- **PATCH**: bug fix or documentation correction.

Current version is defined in `pyproject.toml` (and surfaced in `README.md`).

## What needs updating for a release

Before cutting a release `vX.Y.Z`, update these files:

- `pyproject.toml` (`[project].version`)
- `README.md` (“Current release: …”)
- `CHANGELOG.md` (move entries from `[Unreleased]` into a new `[X.Y.Z]` section)

Notes:

- Sphinx does not need a separate version bump here unless you explicitly surface it in docs pages.
- If behaviour changed (deployment, demo/real mode, suppression semantics), update the relevant docs pages as part of the release.

## Pre-release verification checklist (local)

Run these from the project root using the project virtual environment at `.venv`.

For the closest local equivalent to the repository quality gates in one command, run:

```bash
scripts/run_quality_checks.sh
```

You can still use the explicit checklist below when you want to run or debug individual stages separately.

### 1) Install dependencies (clean env)

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r docs/requirements-docs.txt
```

### 2) Formatting

```bash
ruff check .
ruff format .
```

### 3) Tests (unit + integration)

```bash
pytest tests/ -v --tb=short -m "not e2e"
```

Optional (coverage):

```bash
pytest tests/ -m "not e2e" --cov=src --cov-report=term-missing --cov-fail-under=57
```

### 4) Type checking

```bash
mypy src/ tests/ --config-file pyproject.toml
```

### 5) Security audit (dependencies)

```bash
XDG_CACHE_HOME=/tmp pip-audit
bandit -q -r src references/SROI_Wales_Voluntary_Sector/scripts tools
git ls-files -z | xargs -0 detect-secrets-hook --baseline .secrets.baseline
```

### 6) Packaging validation

```bash
python -m build --sdist --wheel --no-isolation
```

### 7) Documentation build (diagrams + Sphinx)

```bash
python scripts/generate_diagrams.py
sphinx-build -b html docs/source docs/build/html
```

## Release steps (git + GitHub)

### 1) Ensure the changelog is ready

- `CHANGELOG.md` has a new section for `X.Y.Z` with:
  - Added / Changed / Fixed entries
  - the release date
- `[Unreleased]` exists again after the release section (empty stub is fine).

### 2) Commit the release prep

The release commit should include the version bumps and changelog entry.

### 3) Create an annotated tag

Use an annotated tag with the format `vX.Y.Z`:

```bash
git tag -a "vX.Y.Z" -m "vX.Y.Z"
```

### 4) Push branch and tag

```bash
git push
git push --tags
```

### 5) Publish a GitHub Release

- Create a GitHub Release for tag `vX.Y.Z`.
- Paste the `CHANGELOG.md` entry for `X.Y.Z` into the release notes.
- If there are operational changes, call them out explicitly (dataset resolution, demo mode, secrets, deployment health expectations).

## CI requirements for a release

The canonical CI workflow is `.github/workflows/ci.yml`. A release commit should have green status for:

- tests (Python 3.11 and 3.12) with coverage artefact
- lint (Ruff + import-linter contracts)
- typecheck (mypy)
- security (pip-audit, Bandit, detect-secrets)
- packaging (sdist and wheel build)
- docs build (diagrams + Sphinx HTML)
- e2e smoke import (Streamlit app import)

If CI is red, fix CI first. Do not “release around” a failing pipeline.

The local `scripts/run_quality_checks.sh` runner is intended to give contributors a one-command way to exercise the same categories of checks before pushing.

## Post-release hygiene

- Ensure `CHANGELOG.md` has an empty `[Unreleased]` section at the top.
- If the release changed runtime expectations, verify:
  - the **Deployment Health** page reports the expected app mode (`demo` vs `real`),
  - the operator runbook remains accurate (`operations_runbook`), and
  - secrets guidance remains accurate (`02_private_data_secrets_and_demo_mode`).
