..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

Privacy and suppression
=======================

This page explains how the dashboard protects respondent anonymity, why some
views may show **suppressed** results, and how to interpret disappearing
segments when filters are tight.

K-anonymity and small-n suppression
-----------------------------------

The app uses a simple **k-anonymity** rule to protect organisations from being
individually identifiable in charts and tables.

Threshold
^^^^^^^^^

- The global threshold is ``K_ANON_THRESHOLD = 5`` organisations.
- When the current filtered sample contains fewer than 5 organisations:

  - The sidebar shows a warning:

    - “Only **n** organisations match these filters (below the privacy threshold of 5).
      Results are suppressed to protect respondent anonymity.”

  - Pages that honour suppression (e.g. **Overview**, **Executive Summary**) will:

    - Show a suppression warning.
    - Stop rendering detailed charts/tables for that view.

Why slices disappear
^^^^^^^^^^^^^^^^^^^^

Charts and tables may hide or grey out:

- Very small **segments** (e.g. a particular main activity with only 2–3
  respondents in the current filters).
- Particular **cross-tab combinations** (e.g. LA + staff size + concern) where
  the base is too small for a stable percentage.

This is intentional. It avoids revealing information about individual
organisations or very small groups, while still allowing robust, higher-level
patterns to be explored.

Where suppression is applied
----------------------------

Global filter suppression
^^^^^^^^^^^^^^^^^^^^^^^^^

- The core suppression flag is computed in ``src/app.py``:

  - ``ui_config.suppressed = n < K_ANON_THRESHOLD``

  where ``n`` is the number of organisations after applying all sidebar filters.

- Pages that respect the global flag include:

  - **Overview**
  - **Executive Summary**

  These pages show a clear warning and call ``st.stop()`` when suppression is on.

Per-metric and per-segment rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some helpers carry additional **base_n** and **enough_data** flags so that
per-segment tiles can be treated cautiously even when the overall filtered
sample is large.

Examples:

- ``cross_segment_analysis`` in ``src/eda.py``:

  - Drops segments with fewer than 3 organisations.
  - Adds, for each metric:

    - ``*_base_n``: the non-missing base used for that percentage.
    - ``*_enough_data``: whether base_n ≥ the segment minimum.

- ``finance_recruitment_cross``:

  - Returns ``None`` instead of a comparison when either finance group has
    fewer than 3 organisations, or the total sample is too small.

UI code can use these flags to:

- Omit unstable tiles.
- Grey out segments that technically exist but don’t meet agreed minimum bases.

Demo mode vs real mode
----------------------

Demo mode
^^^^^^^^^

When the real Wave 2 dataset is not configured or cannot be loaded, the app
falls back to a **bundled sample fixture** (under ``tests/fixtures/``) and
enters explicit **demo mode**.

In demo mode:

- The sidebar caption shows **DEMO / SAMPLE DATA**.
- A warning banner explains that figures are for demonstration only.
- Deployment Health reports ``app_mode = "demo"`` and the dataset source as
  ``sample_path``.
- Presentation outputs are labelled as demo according to
  ``get_demo_output_mode()`` in ``src.config``.

Real mode
^^^^^^^^^

When a real dataset path or URL is resolved:

- ``RuntimeDataSource.is_demo`` is ``False``.
- Deployment Health reports ``app_mode = "real"``.
- The sidebar does not show demo labelling.

Demo mode is safe for:

- Documentation builds (Sphinx / Read the Docs).
- CI smoke tests.
- Training or show-and-tell environments.

It should **not** be used to brief on real Wave findings.

Operator checklists
-------------------

For operators and deployment engineers:

- Review ``docs/learning/02_private_data_secrets_and_demo_mode.md`` for:

  - The runtime resolution order for datasets and context.
  - Environment/secrets configuration examples.
  - Demo-vs-real behaviour in the app and presentation generator.

- Use the :doc:`operations_runbook` for:

  - “App is red” troubleshooting.
  - Reading **Deployment Health** correctly.
  - Fixing common misconfigurations without exposing private data.

Cross-links
-----------

- Data Notes page (in-app):

  - Includes a short bullet point on privacy and suppression and can be
    extended to link back to this page for more detail.

- README and deployment docs:

  - Point operators to:

    - :doc:`deployment_checklist`
    - :doc:`operations_runbook`
    - :doc:`privacy_and_suppression`
