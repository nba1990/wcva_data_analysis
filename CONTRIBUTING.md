<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Contributing to WCVA Baromedr Cymru Wave 2 Dashboard

Thank you for your interest in contributing. This document explains how to set up your environment, run checks locally, and submit changes.

---

## 1. Development setup

- **Python**: 3.11 or 3.12 (see `pyproject.toml` and CI).
- **Clone and install**:
  ```bash
  git clone <repository-url>
  cd wcva_data_analysis
  python -m venv .venv
  source .venv/bin/activate   # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **Optional – pre-commit hooks** (run Black, isort, and tests before each commit):
  ```bash
  pip install pre-commit
  pre-commit install
  ```
  After this, `git commit` will run the hooks. Run manually with: `pre-commit run --all-files`.

---

## 2. Before you submit

1. **Tests**: From the project root, run:
   ```bash
   pytest
   ```
   To exclude end-to-end tests (e.g. if you don't have a Streamlit runtime):
   ```bash
   pytest -m "not e2e"
   ```
   To run with coverage: `pytest tests/ -m "not e2e" --cov=src --cov-report=term-missing`. See `docs/LEARNING_AND_BACKLOG.md` (§3.2) for coverage goals.

2. **Formatting**: The project uses **Black** and **isort**. CI will fail if files are not formatted.
   ```bash
   black src/ tests/
   isort src/ tests/
   ```
   Or use pre-commit (above) to do this automatically.

3. **Type checking** (optional): If mypy is configured, run:
   ```bash
   mypy src/
   ```

4. **Logging and observability**:
   - Use the shared `WCVA_LOGGER` from `src.config` instead of creating new loggers.
   - Prefer structured logs with `extra={...}` for key fields (for example: `{"app_mode": "demo", "n_rows": len(df)}`).
   - Log configuration and data-source decisions at **INFO**; use **WARNING** for insecure or unexpected but recoverable situations; use **ERROR** when a request or page cannot proceed.

5. **Secrets scanning (detect-secrets)**:
   - This repo is configured to use [`detect-secrets`](https://github.com/Yelp/detect-secrets) via pre-commit.
   - To (re)generate the baseline after installing `detect-secrets`:
     ```bash
     detect-secrets scan > .secrets.baseline
     ```
   - The `.pre-commit-config.yaml` hook uses this baseline:
     ```yaml
     - id: detect-secrets
       name: detect-secrets (scan for secrets)
       entry: .venv/bin/detect-secrets-hook --baseline .secrets.baseline
       language: system
       pass_filenames: true
     ```
   - After updating the baseline, run:
     ```bash
     pre-commit run detect-secrets --all-files
     ```

   Secrets scanning does not replace good operational hygiene (see
   `docs/DOCKER_AND_DEPLOYMENT.md` and
   `docs/learning/02_private_data_secrets_and_demo_mode.md`), but it adds another
   automated safety net.

---

## 3. Branching and pull requests

- Use a **feature branch** (e.g. `feature/short-description` or `fix/issue-description`).
- Keep changes focused; prefer several small PRs over one large one.
- **Pull requests** should:
  - Describe what changed and why.
  - Reference any related issues.
  - Ensure CI passes (tests, lint, and any other checks).

The maintainers may ask for adjustments; once approved, your PR will be merged.

---

## 4. Documentation (Sphinx)

To build the project documentation (getting started, architecture, API reference):

```bash
pip install -r requirements.txt
pip install -r docs/requirements-docs.txt
cd docs && make html
```

Output is in `docs/build/html/`; open `index.html` in a browser. The API reference is generated from the same docstrings and type hints you add in code (see §7). When you run the build, Streamlit may print warnings (e.g. "No runtime found", "missing ScriptRunContext") because Sphinx imports the app outside a Streamlit run; these are expected and can be ignored.

The public hosted documentation is available on Read the Docs at `https://baromedr.readthedocs.io/en/latest/`.

---

## 5. Where to look

- **Architecture and design**: `ARCHITECTURE.md`, and the ADRs in `docs/adr/` (e.g. ADR-004 for state/caching, ADR-005 for Docker, ADR-006 for CI and testing).
- **Adding a new page**: See README “SROI & References” and ARCHITECTURE “Where to look when extending the app”.
- **Testing strategy**: `docs/LEARNING_AND_BACKLOG.md` (§3).
- **Backlog and policy context**: `docs/LEARNING_AND_BACKLOG.md`, `plans/policy_questions.md`.

---

## 6. Code and behaviour

- **Session state**: Per-user state lives in `st.session_state`; use `get_app_ui_config()` from `src.config` for the UI config. Do not use module-level mutable globals for per-request data (see ADR-004).
- **Caching**: Use `st.cache_data` for read-only data loading; keep heavy or shared resources in `st.cache_resource` where appropriate.
- **Style**: Follow Black and isort; use type hints for function parameters and return values where they add clarity.
- **Docstrings**: Public functions and modules should have a short docstring; use comprehensive docstrings for non-obvious behaviour (e.g. EDA helpers, config grouping).

---

## 7. Documentation and code standards

The codebase aims for **comprehensive coverage** of docstrings and type information:

- **Module docstrings**: Each `src` module has a top-level docstring describing what the module provides (e.g. main functions, key types, usage).
- **Class docstrings**: Document the purpose and list **Attributes** (name, type, meaning) for dataclasses and important classes (e.g. `StreamlitAppUISharedConfigState`, `AltTextConfig`, `NavItem`).
- **Function docstrings**: Use a short summary line; for public and non-obvious functions add **Args** (parameter name, type, meaning) and **Returns** (type and meaning). Use "Args"/"Returns" style (Google-style) for consistency.
- **Type hints**: Use type hints for function parameters and return types (e.g. `df: pd.DataFrame`, `-> dict[str, Any]`, `path: str | None = None`). For EDA and data_loader-style functions that return dicts with mixed value types (DataFrames, scalars, nested dicts), use `dict[str, Any]` or `list[dict[str, Any]]` so mypy accepts attribute access on values. Typing in tests is encouraged where it helps readability.
- **Variables**: For complex or non-obvious variables, a brief inline comment is sufficient; key constants (e.g. in `config.py`) are documented via module or section comments.

When adding new code, extend this standard: add a module docstring if you create a new module, and add Args/Returns to new public functions. See existing modules (`src/data_loader.py`, `src/config.py`, `src/eda.py`, `src/charts.py`) for examples.

---

## 8. Releases and versioning

- Use lightweight semantic versioning:
  - `MAJOR` for breaking changes to runtime or deployment expectations.
  - `MINOR` for new dashboard capabilities, documentation, deployment, or testing improvements that remain backwards-compatible.
  - `PATCH` for focused bug fixes or documentation corrections.
- The canonical release runbook lives in **`docs/source/release_process.md`** (Sphinx: *Release process*). Use that page as the single source of truth.
- Before a release, update:
  - `pyproject.toml` (version)
  - `README.md` (Current release)
  - `CHANGELOG.md` (Keep a Changelog format)
- Create an annotated git tag using the format `vX.Y.Z` and publish a matching GitHub Release.
- Keep `CHANGELOG.md` in Keep a Changelog style with a fresh `Unreleased` section after each release.

If you have questions, open an issue or start a discussion through the repository.
