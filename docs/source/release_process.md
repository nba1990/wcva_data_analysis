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

### 1) Install dependencies (clean env)

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r docs/requirements-docs.txt
```

### 2) Formatting

```bash
black src/ tests/
isort src/ tests/
```

### 3) Tests (unit + integration)

```bash
pytest tests/ -v --tb=short -m "not e2e"
```

Optional (coverage):

```bash
pytest tests/ -m "not e2e" --cov=src --cov-report=term-missing
```

### 4) Type checking

```bash
mypy src/ tests/ --config-file pyproject.toml
```

### 5) Security audit (dependencies)

```bash
pip-audit
```

### 6) Documentation build (diagrams + Sphinx)

```bash
python scripts/generate_diagrams.py
cd docs && make html
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
- lint (Black/isort + import-linter contracts)
- typecheck (mypy)
- security (pip-audit)
- docs build (diagrams + Sphinx HTML)
- e2e smoke import (Streamlit app import)

If CI is red, fix CI first. Do not “release around” a failing pipeline.

## Post-release hygiene

- Ensure `CHANGELOG.md` has an empty `[Unreleased]` section at the top.
- If the release changed runtime expectations, verify:
  - the **Deployment Health** page reports the expected app mode (`demo` vs `real`),
  - the operator runbook remains accurate (`operations_runbook`), and
  - secrets guidance remains accurate (`02_private_data_secrets_and_demo_mode`).
