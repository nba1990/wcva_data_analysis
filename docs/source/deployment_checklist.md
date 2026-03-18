---
title: Deployment checklist
---

# Deployment checklist

This page is for operators who deploy or maintain the Baromedr Cymru dashboard.

It summarises the key runtime expectations and links back to the detailed docs.

## 1. Environment and dependencies

- **Python version**: 3.11 or 3.12 (see `README.md`).
- **Dependencies**:
  - Install `requirements.txt` (application).
  - For building docs and diagrams in CI or admin environments, also install `docs/requirements-docs.txt`.
- **Container option**:
  - You can run the app via `Dockerfile` / `docker-compose.yml`; see `docs/DOCKER_AND_DEPLOYMENT.md` for details.

## 2. Runtime data configuration

The app resolves runtime data sources via `src.config.resolve_dataset_source()` and `src.config.resolve_la_context_source()`:

- **Wave dataset (private)**:
  - Preferred:
    - `WCVA_DATASET_PATH` (filesystem path) **or**
    - `dataset_path` in Streamlit secrets.
  - Fallbacks:
    - `WCVA_DATASET_URL` (HTTP/HTTPS) **or**
    - `dataset_url` in Streamlit secrets.
  - If none of these resolve to a usable file/URL, the app falls back to the bundled sample fixture and enters **demo mode**.

- **Local-authority context (public)**:
  - Preferred:
    - `WCVA_LA_CONTEXT_PATH` (filesystem path) **or**
    - `la_context_path` in Streamlit secrets.
  - Fallbacks:
    - `WCVA_LA_CONTEXT_URL` **or**
    - `la_context_url` in Streamlit secrets.
  - If none are set, the app uses `references/context/la_context_wales.csv` bundled in the repo.

These rules are documented in `src/config.py`, `src/data_loader.py`, and `ARCHITECTURE.md` (“Runtime data and demo mode”).

## 3. Deployment Health page

Before trusting a deployment, visit the **Deployment Health** page in the app:

- Confirms:
  - Whether the app is running in **demo** or **real data** mode.
  - Presence of required and optional runtime files (from `data_loader.check_runtime_assets()`).
  - Basic dataset shape when data is loaded (`rows`, `columns`, presence of derived `region` column).
- Shows **resolved runtime sources** for:
  - Wave dataset.
  - Local-authority context.
- Provides **masked resolution attempts** (environment variables, secrets, defaults) so you can see what was tried without exposing sensitive values.

If required files are missing or the app is stuck in demo mode, use this page together with your environment/secrets configuration to diagnose the issue.

## 4. CI expectations

The main GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

- `test` – unit and integration tests with coverage on Python 3.11 and 3.12.
- `e2e-smoke` – Streamlit import smoke test.
- `lint` – Ruff and Import Linter (architecture contracts).
- `typecheck` – mypy over `src/` and `tests/`.
- `security` – `pip-audit` to check for known vulnerabilities.
- `docs` – diagram generation (`scripts/generate_diagrams.py`) and Sphinx HTML build.

For releases or production deployments, all of these jobs should be green for the target commit.

For local reproduction of CI, see the “Local CI checklist” section in `docs/source/contributing.rst`.
