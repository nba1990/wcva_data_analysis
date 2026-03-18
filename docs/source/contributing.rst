..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

Contributing
=============

This page points you to the main contributing guide and highlights the main steps. The full text is in the repository: **CONTRIBUTING.md**.

Setup and checks
----------------

1. **Development setup**: Python 3.11 or 3.12, ``pip install -r requirements.txt`` and ``pip install -r requirements-dev.txt``. Optional: pre-commit for Ruff, mypy, import-linter, and tests.
2. **One-shot local validation**: Run ``scripts/run_quality_checks.sh`` for the broader local quality suite, or ``scripts/run_quality_checks.sh --quick`` for the faster day-to-day subset. In full mode, ``pip-audit`` needs outbound network access to query vulnerability data.
3. **Tests**: Run ``pytest`` (or ``pytest -m "not e2e"`` to skip end-to-end tests). Use ``pytest tests/ -m "not e2e" --cov=src --cov-report=term-missing`` for coverage.
4. **Formatting and linting**: ``ruff check .`` and ``ruff format .`` so CI passes.
5. **Type checking**: ``mypy src/`` (see ``pyproject.toml``).
6. **Architecture contracts**: ``lint-imports``.

Branching and pull requests
---------------------------

* Use a feature branch; keep changes focused.
* Pull requests should describe what changed and why, reference issues if any, and ensure CI passes.

Code and documentation standards
---------------------------------

* **Session state**: Per-user state in ``st.session_state``; use ``get_app_ui_config()`` from ``src.config``. No module-level mutable globals for per-request data (see ADR-004).
* **Caching**: ``st.cache_data`` for read-only data; ``st.cache_resource`` for heavy shared resources.
* **Style**: Ruff formatting and linting; type hints on parameters and return values.
* **Docstrings**: Module and function docstrings; use Args/Returns for public and non-obvious behaviour. See CONTRIBUTING.md §7 for the full documentation and typing standard.

* **Architecture diagrams**:
  - High-level diagrams live under :doc:`architecture` (Mermaid for flows, Graphviz for code-derived structure).
  - To regenerate code-derived diagrams locally, run ``python scripts/generate_diagrams.py`` from the project root and then ``cd docs && make html``.
  - The broader ``scripts/run_quality_checks.sh`` runner includes diagram generation and the Sphinx HTML build in its default ``--full`` mode.
  - Read :doc:`architecture/reading_diagrams` for details on how to interpret the diagrams and how RTD builds them.

Where to look
-------------

* **Architecture**: ``ARCHITECTURE.md`` and ``docs/adr/``.
* **Adding a page**: README “SROI & References” and ARCHITECTURE “Where to look when extending the app”.
* **Testing strategy**: ``docs/LEARNING_AND_BACKLOG.md`` §3.
* **Backlog and policy**: ``docs/LEARNING_AND_BACKLOG.md``, ``plans/policy_questions.md``.
