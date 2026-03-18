---
title: Streamlit pages & navigation
---

# Streamlit pages & navigation

```{mermaid}
flowchart LR
  sidebar["Sidebar navigation (navigation.render_sidebar_nav)"]

  sidebar --> atAGlance["at_a_glance.render_page()"]
  sidebar --> execSummary["executive_summary.render_page()"]
  sidebar --> overview["overview.render_page()"]
  sidebar --> deploymentHealth["deployment_health.render_page()"]
  sidebar --> demographics["demographics_and_types.render_page()"]
  sidebar --> concerns["concerns_and_risks.render_page()"]
  sidebar --> trends["trends_and_waves.render_page()"]
  sidebar --> volunteerRecruit["volunteer_recruitment.render_page()"]
  sidebar --> volunteerRetain["volunteer_retention.render_page()"]
  sidebar --> workforce["workforce_and_operations.render_page()"]
  sidebar --> dataNotes["data_notes.render_page()"]
  sidebar --> earnedSettlement["earned_settlement.render_page()"]
  sidebar --> sroiRefs["sroi_references.render_page()"]
```

How to read this diagram:

- Each arrow from ``sidebar`` points to a module in :mod:`src.section_pages` that exposes a single render function (usually ``render_page`` or ``render_main``).
- The sidebar itself is rendered by :func:`src.navigation.render_sidebar_nav`, using a list of :class:`src.navigation.NavItem` objects.
- The current page is dispatched from :mod:`src.app` based on the selected navigation ID.

Modules behind each node:

- ``at_a_glance.render_page()`` → :mod:`src.section_pages.at_a_glance`
- ``executive_summary.render_page()`` → :mod:`src.section_pages.executive_summary`
- ``overview.render_page()`` → :mod:`src.section_pages.overview`
- ``deployment_health.render_page()`` → :mod:`src.section_pages.deployment_health`
- ``demographics_and_types.render_page()`` → :mod:`src.section_pages.demographics_and_types`
- ``concerns_and_risks.render_page()`` → :mod:`src.section_pages.concerns_and_risks`
- ``trends_and_waves.render_page()`` → :mod:`src.section_pages.trends_and_waves`
- ``volunteer_recruitment.render_page()`` → :mod:`src.section_pages.volunteer_recruitment`
- ``volunteer_retention.render_page()`` → :mod:`src.section_pages.volunteer_retention`
- ``workforce_and_operations.render_page()`` → :mod:`src.section_pages.workforce_and_operations`
- ``data_notes.render_page()`` → :mod:`src.section_pages.data_notes`
- ``earned_settlement.render_page()`` → :mod:`src.section_pages.earned_settlement`
- ``sroi_references.render_page()`` → :mod:`src.section_pages.sroi_references`

Notes:

- The exact function names may differ slightly (e.g. ``render_main`` vs ``render_page``), but each module in :mod:`src.section_pages` exposes a single render function that the navigation layer calls.
- Navigation IDs are defined in :class:`src.navigation.NavItem` instances and must stay in sync with the dispatch logic in :mod:`src.app`.
- This structure makes it easy to **add a new page**: create a new module under :mod:`src.section_pages`, implement ``render_*``, and register it in :mod:`src.navigation` and the app dispatch.

To see how these pages sit in the wider module graph, compare this view with :doc:`module_dependencies` and :doc:`class_hierarchy`. For API-level details of each module, see :doc:`api/index`.
