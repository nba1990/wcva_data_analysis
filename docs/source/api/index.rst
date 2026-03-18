..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

API Reference
=============

This section documents the main Python modules and packages.

If you're following the :doc:`architecture` pages, you can think of the API in four layers:

- **Core runtime & configuration** – app entry point, navigation, and config.
- **Data loading & analysis** – how CSVs are resolved, loaded, and transformed.
- **Charts & UI helpers** – reusable Plotly/Streamlit helpers and visual building blocks.
- **Pages & narratives** – section page modules and narrative text helpers.

Core runtime & configuration
----------------------------

.. autosummary::
   :toctree: core
   :nosignatures:

   src.app
   src.navigation
   src.config

Data loading & analysis
-----------------------

.. autosummary::
   :toctree: analysis
   :nosignatures:

   src.data_loader
   src.eda
   src.wave_context

Charts & UI helpers
-------------------

.. autosummary::
   :toctree: ui
   :nosignatures:

   src.charts
   src.sroi_charts.sroi_figures
   src.infographic

Pages & narratives
------------------

.. autosummary::
   :toctree: pages
   :nosignatures:

   src.section_pages
   src.narratives
