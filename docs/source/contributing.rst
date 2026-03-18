..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

Contributing
=============

This page points you to the main contributing guide and highlights the main steps. The full text is in the repository: **CONTRIBUTING.md**.

Setup and checks
----------------

1. **Development setup**: Python 3.11 or 3.12, ``pip install -r requirements.txt``. Optional: pre-commit for Black, isort, and tests.
2. **Tests**: Run ``pytest`` (or ``pytest -m "not e2e"`` to skip end-to-end tests). Use ``pytest tests/ -m "not e2e" --cov=src --cov-report=term-missing`` for coverage.
3. **Formatting**: ``black src/ tests/`` and ``isort src/ tests/`` so CI passes.
4. **Type checking**: ``mypy src/`` if mypy is configured (see pyproject.toml).

Branching and pull requests
---------------------------

* Use a feature branch; keep changes focused.
* Pull requests should describe what changed and why, reference issues if any, and ensure CI passes.

Code and documentation standards
---------------------------------

* **Session state**: Per-user state in ``st.session_state``; use ``get_app_ui_config()`` from ``src.config``. No module-level mutable globals for per-request data (see ADR-004).
* **Caching**: ``st.cache_data`` for read-only data; ``st.cache_resource`` for heavy shared resources.
* **Style**: Black and isort; type hints on parameters and return values.
* **Docstrings**: Module and function docstrings; use Args/Returns for public and non-obvious behaviour. See CONTRIBUTING.md §7 for the full documentation and typing standard.

* **Architecture diagrams**:
  - High-level diagrams live under :doc:`architecture` (Mermaid for flows, Graphviz for code-derived structure).
  - To regenerate code-derived diagrams locally, run ``python scripts/generate_diagrams.py`` from the project root and then ``cd docs && make html``.
  - Read :doc:`architecture/reading_diagrams` for details on how to interpret the diagrams and how RTD builds them.

Where to look
-------------

* **Architecture**: ``ARCHITECTURE.md`` and ``docs/adr/``.
* **Adding a page**: README “SROI & References” and ARCHITECTURE “Where to look when extending the app”.
* **Testing strategy**: ``docs/LEARNING_AND_BACKLOG.md`` §3.
* **Backlog and policy**: ``docs/LEARNING_AND_BACKLOG.md``, ``plans/policy_questions.md``.
