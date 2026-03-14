# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Changed

- Release preparation for `0.2.0`, including aligned version metadata and clearer Streamlit Community Cloud deployment guidance.

---

## [0.2.0] - 2026-03-14

### Added

- **Sphinx documentation**: Built docs (getting started, architecture, contributing, API reference) in `docs/source/`; build with `pip install -r docs/requirements-docs.txt` then `cd docs && make html`. Output in `docs/build/html/`. See README and CONTRIBUTING §4.
- **Fixture for executive highlights**: `tests/fixtures/wcva_sample_dataset.csv` extended with multi-select columns so `test_executive_highlights_structure_on_fixture` runs without skipping.
- **CI**: Single GitHub Actions workflow (`.github/workflows/ci.yml`) with test (Python 3.11, 3.12), e2e smoke (app import), lint (Black, isort), typecheck (mypy), and security (pip audit). Coverage reported as artifact. Rationale recorded in ADR-006.
- **Pre-commit**: `.pre-commit-config.yaml` for Black, isort, and pytest (non-e2e). Optional local use; see CONTRIBUTING.
- **CONTRIBUTING.md**: Development setup, pre-commit, branching, and PR guidelines.
- **CHANGELOG.md**: This file.
- **GitHub templates**: Issue and pull request templates under `.github/`.
- **Docs**: Tested-with Python 3.11/3.12 and optional dependency pinning in README; security/secrets note in README and Docker deployment doc; CI and test run details in `docs/LEARNING_AND_BACKLOG.md`.

### Changed

- **Session state**: UI config is per-session via `get_app_ui_config()` and `st.session_state["app_ui_config"]`; removed module-level singleton (see ADR-004).
- **Performance**: Cached `load_la_context()`, cached SROI mind-map HTML, removed unnecessary `df_full.copy()`, optional `WCVA_DEBUG_MEMORY` for sidebar memory display.
- **Deployment**: Docker and docker-compose added; see `docs/DOCKER_AND_DEPLOYMENT.md` and ADR-005.
- **Tests**: `pytest.ini` added with `e2e` marker; `tests/conftest.py` now adds project root to `sys.path` (fixed legacy path). Empty-dataframe edge case in `workforce_operations` no longer raises RuntimeWarning.
- **Linting**: Black and isort applied; `pyproject.toml` holds config. Mypy added with gradual typing; unused `type: ignore` removed in `narratives.py` and `eda.py`.
- **Documentation and typing**: Comprehensive docstrings (module, class, function with Args/Returns) and type hints across `src/` (data_loader, config, eda, charts, navigation, narratives, section_pages, wave_context, infographic, sroi_figures, app). CONTRIBUTING §7 documents the standard. EDA and data_loader return types use `dict[str, Any]` / `list[dict[str, Any]]` for flexible values (mypy-clean).

### Fixed

- **GitHub Actions**: Replaced broken Conda and Pylint workflows with pip-based CI (tests, lint, typecheck, security, e2e smoke).
- **Mypy**: EDA, data_loader, section_pages, and generate_presentation now use `dict[str, Any]` / `list[dict[str, Any]]` for mixed-type output dicts so mypy accepts attribute access on values; CONTRIBUTING §7 and CHANGELOG updated to match.

---

## [0.1.0] - earlier

- Initial WCVA Baromedr Cymru Wave 2 dashboard (Streamlit, multi-page, filters, SROI references, k-anonymity suppression).
- ADRs 001–004 (Streamlit, navigation, SROI charts, state and caching).
