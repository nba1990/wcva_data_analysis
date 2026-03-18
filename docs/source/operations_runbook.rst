..
   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
   SPDX-License-Identifier: AGPL-3.0-or-later
   See the LICENSE file for full licensing terms.

Operations runbook
==================

This page is for **operators and maintainers** of the Baromedr Cymru Wave 2 dashboard.
It summarises what to check when the app is red, how to interpret **Deployment Health**,
and how to fix the most common misconfigurations in production.

When the app is red
-------------------

Use this checklist when the dashboard is not behaving as expected:

1. **Can you reach the app UI?**

   - If the browser cannot connect at all:

     - For Docker/self-hosting:

       - Run ``docker compose ps`` (or ``docker ps``) and confirm the container is **Up**.
       - Check that port **8501** is exposed and that the reverse proxy (Nginx, Caddy, etc.)
         is pointing at the right host/port.
       - Inspect container logs with ``docker compose logs`` and look for Python tracebacks.

     - For Streamlit Community Cloud:

       - Open the **Logs** tab in the app dashboard.
       - Look for import errors, missing packages, or dataset path/URL issues.

2. **Does the app start in demo mode?**

   - The sidebar caption and **Deployment Health** page will clearly say **DEMO / SAMPLE DATA**
     when the real Wave dataset is not configured.
   - Demo mode is safe for docs, training, and smoke tests, but is **not** suitable for
     real Wave analysis.

   If you see demo mode unexpectedly:

   - Check that one of the following is configured and reachable:

     - ``WCVA_DATASET_PATH``
     - ``dataset_path`` in Streamlit secrets
     - ``WCVA_DATASET_URL``
     - ``dataset_url`` in Streamlit secrets

   - Confirm the file exists or the URL returns a CSV.
   - Review the masked resolution attempts in **Deployment Health → Dataset source
     resolution attempts** to see which candidates were tried.

3. **Are filters causing suppression?**

   - If pages show **“Results suppressed due to small sample size”** or similar warnings:

     - The filtered sample has fewer than ``K_ANON_THRESHOLD`` organisations
       (default: **5**), so the app intentionally hides charts/tables.
     - Widen or clear filters (size, LA, activity, concerns) to bring the base
       above the threshold.

   - Use the sidebar caption (“Showing **n** of N organisations”) to see the current base.

4. **Is a single page failing?**

   - Pages are wrapped in a small error boundary. If one page fails:

     - You will see an error message on that page suggesting:

       - Trying another page.
       - Reviewing **Deployment Health**.
       - Checking server logs.

     - Other pages and navigation should still work.

   - Check logs for recent tracebacks mentioning the failing page module under
     ``src/section_pages/`` and raise an issue with the maintainer team if needed.

Reading Deployment Health
-------------------------

The **Deployment Health** page is your primary diagnostic tool. It reports:

- **App mode**:

  - **Real data** – a non-demo dataset was resolved.
  - **Demo** – the bundled sample fixture is being used instead.

- **Missing required / optional assets**:

  - Required:

    - Wave 2 dataset source (path or URL)
    - Streamlit config (theme and server settings)

  - Optional:

    - Local-authority context CSV
    - SROI mind-map HTML
    - SROI briefing PDF

- **Resolved runtime sources**:

  - Masked paths/URLs for:

    - Wave dataset (including demo vs real mode, file vs URL)
    - Local-authority context

- **Session-level mode counters**:

  - How many times demo vs real modes have been used since startup.

Recommended workflow:

1. Open **Deployment Health** immediately after a new deploy.
2. Confirm:

   - App mode is **Real data** for production environments.
   - All required assets are present.
   - Optional assets exist where you expect them (especially SROI files).
3. Use the **Download diagnostics JSON** button to capture:

   - Masked dataset and context metadata.
   - Basic dataset shape (rows, columns).

   This file can be attached to support tickets without leaking private URLs.

Common misconfigurations and fixes
----------------------------------

Missing or misconfigured dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Symptoms:

- App shows **demo mode** warnings.
- Deployment Health reports missing Wave 2 dataset source.
- Logs mention ``Wave 2 dataset not found``.

Steps:

1. Decide whether you are using a **local file** or a **private URL**.
2. For a local file:

   - Place the CSV outside Git (e.g. ``/app/runtime-data/WCVA_W2_Anonymised_Dataset.csv``).
   - Set ``WCVA_DATASET_PATH`` to that absolute path, or use ``dataset_path`` in
     Streamlit secrets.

3. For a private URL:

   - Use an HTTPS, access-controlled endpoint (e.g. presigned S3).
   - Set ``WCVA_DATASET_URL`` or ``dataset_url`` in Streamlit secrets.
   - Avoid long-lived public HTTP URLs; the app will log a warning for non-HTTPS.

4. Restart the app and re-check **Deployment Health**.

For detailed guidance, see :doc:`deployment_checklist` and
``docs/DOCKER_AND_DEPLOYMENT.md``.

Local-authority context issues
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Symptoms:

- Geography tables/charts look empty or incomplete.
- Deployment Health reports missing **Local authority context CSV**.

Steps:

1. If you are happy with the **public default**, ensure:

   - ``references/context/la_context_wales.csv`` is present in the deployed image
     or volume.

2. If you are overriding the context:

   - Check ``WCVA_LA_CONTEXT_PATH`` / ``WCVA_LA_CONTEXT_URL`` or the matching
     Streamlit secrets.
   - Confirm the override file/URL exists and has the expected columns.

3. Revisit **Deployment Health** and verify the resolved LA context source.

Secrets and environment hygiene
-------------------------------

This dashboard is designed so that **private data never needs to appear in Git**.
Follow the checklists in:

- ``docs/DOCKER_AND_DEPLOYMENT.md`` – “Secrets and runtime configuration: quick do/don’t checklist”.
- ``docs/learning/02_private_data_secrets_and_demo_mode.md`` – “Secrets and env hygiene checklist”.

Key points:

- Keep private survey datasets and credentials **out of Git history and Docker images**.
- Treat dataset URLs as **secrets**, especially when they are presigned.
- Use environment variables or secret managers (Streamlit Secrets, AWS Secrets Manager, etc.).
- Do not log raw paths or URLs; rely on the masking helpers in ``src.config``.

For more background on demo mode, runtime resolution, and masking, see
``docs/learning/02_private_data_secrets_and_demo_mode.md`` and
the :doc:`privacy_and_suppression` page.

Links to other docs
-------------------

- :doc:`deployment_checklist`
- :doc:`getting_started`
- :doc:`architecture`
- :doc:`privacy_and_suppression`
