.. Baromedr Cymru Wave 2 Dashboard documentation master file

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

Quick links
-----------

* **Run the dashboard**: ``streamlit run src/app.py`` (see :doc:`getting_started`).
* **Project layout**: ``src/app.py`` is the entry point; ``src/section_pages/`` holds each page; ``src/eda.py`` and ``src/data_loader.py`` are the analytical core (see :doc:`architecture`).
* **Tests**: ``pytest -m "not e2e"`` for unit/integration tests; see :doc:`contributing`.
* **API reference**: :doc:`api/index` lists all documented modules and functions.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
