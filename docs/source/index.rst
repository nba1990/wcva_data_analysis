..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

Welcome to Baromedr Cymru Wave 2
================================

This is the documentation for the **Baromedr Cymru Wave 2** interactive analysis dashboard — a Streamlit app for exploring Welsh voluntary sector survey data, with a focus on volunteering, workforce, finances, and SROI evidence.

New users and developers can get oriented here without extra setup: follow the links below to install, run, and understand the codebase.

.. toctree::
   :maxdepth: 2
   :caption: Getting oriented

   getting_started
   architecture
   contributing
   api/index
   deployment_checklist
   operations_runbook
   privacy_and_suppression
   engineering_clusters_and_lifecycle
   capability_clusters
   improvements_review
   release_process

Quick links
-----------

* **Run the dashboard**: ``streamlit run src/app.py`` (see :doc:`getting_started`).
* **Project layout**: ``src/app.py`` is the entry point; ``src/section_pages/`` holds each page; ``src/eda.py`` and ``src/data_loader.py`` are the analytical core (see :doc:`architecture`).
* **Tests**: ``pytest -m "not e2e"`` for unit/integration tests; see :doc:`contributing`.
* **Learning guides**: see ``docs/learning/`` in the repository for curated notes on runtime data, deployment, releases, and git hygiene using this codebase as the example.
* **API reference**: :doc:`api/index` lists all documented modules and functions.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
