..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

Getting started
===============

This page summarises how to install, run, and make a first change so that new users and developers can get going quickly.

Prerequisites
-------------

* **Python**: 3.11 or 3.12.
* **Repository**: Clone the repo and ``cd`` into the project root.

Installation
------------

From the project root:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate    # Windows: .venv\Scripts\activate
   pip install -r requirements.txt

Optional: install pre-commit to run Black, isort, and tests before each commit:

.. code-block:: bash

   pip install pre-commit
   pre-commit install

Run the dashboard
-----------------

.. code-block:: bash

   streamlit run src/app.py

Then open the URL shown in the terminal (typically http://localhost:8501).

Configuration
-------------

* **Data**: Configure the main survey CSV with ``WCVA_DATASET_PATH`` / ``WCVA_DATASET_URL`` or the matching Streamlit secrets keys (``dataset_path`` / ``dataset_url``). For local-only work, an untracked fallback at ``datasets/WCVA_W2_Anonymised_Dataset.csv`` still works.
* **Context data**: The public local-authority context file is checked in at ``references/context/la_context_wales.csv``. Override it only if needed with ``WCVA_LA_CONTEXT_PATH`` / ``WCVA_LA_CONTEXT_URL`` or matching Streamlit secrets.
* **Secrets**: Use Streamlit Secrets (see ``.streamlit/secrets.example.toml``) for private dataset URLs or runtime paths; see the main README.
* **Debug**: Set ``WCVA_DEBUG_MEMORY=1`` to show process memory in the sidebar.
* **Deployment checks**: The app includes a ``Deployment Health`` page and explicit demo-mode fallback to help diagnose missing runtime files in hosted environments.

First steps for developers
---------------------------

1. **Run tests**: ``pytest -m "not e2e"`` (excludes end-to-end Streamlit tests). With coverage: ``pytest tests/ -m "not e2e" --cov=src --cov-report=term-missing``.
2. **Lint**: ``black src/ tests/`` and ``isort src/ tests/`` so CI passes.
3. **Read the architecture**: See :doc:`architecture` for the high-level flow (app → data layer → charts → section pages).
4. **API reference**: See :doc:`api/index` for module and function docs generated from the codebase.

Docker (optional)
-----------------

To run the dashboard in a container:

.. code-block:: bash

   docker compose up --build

See ``docs/DOCKER_AND_DEPLOYMENT.md`` in the repo for full Docker and self-hosting notes.
