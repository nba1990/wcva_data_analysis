# ADR-002 – Navigation model and sidebar UX

## Context

The dashboard grew from a small prototype into a multi-page app covering overview, recruitment, retention, operations, demographics, trends, SROI, and data notes. Early versions used ad‑hoc navigation patterns that made it easy to:

- Forget to wire a new page into the navigation.
- Break links between the visible sidebar and the `if/elif` dispatch in `app.py`.
- Produce inconsistent labels and subtitles across pages.

At the same time, the WCVA brand and user expectations called for:

- A clear, stable sidebar with recognisable icons and short descriptions.
- Robust click behaviour (no “dead” buttons).

## Decision

We centralised navigation into a dedicated module, `src/navigation.py`, with:

- A `NavItem` dataclass describing each page (id, label, subtitle, icon).
- A `NAV_ITEMS` list capturing the full navigation model in one place.
- A single `render_sidebar_nav` function that:
  - Renders the WCVA‑branded sidebar.
  - Manages the current page id via `st.session_state["current_page"]`.
  - Applies consistent styling to active vs inactive items.

The main app (`src/app.py`) uses this module to determine the current page and dispatches to the corresponding `render_*` function in `src/section_pages`.

## Consequences

- Adding or renaming a page now involves:
  - Updating `NAV_ITEMS` in `navigation.py`.
  - Wiring the page id into the `if/elif` dispatch in `app.py`.
  - Implementing a `render_*` function in `src/section_pages`.
- Tests in `tests/unit/test_navigation.py` enforce that:
  - `NAV_ITEMS` ids are unique.
  - Every id appears in the `app.py` dispatch block.
  - Labels and (where present) subtitles are non‑empty.
- Future refactors can evolve toward a more explicit registry (e.g. a `PAGES` dict mapping ids to render functions), but the current pattern already gives a single source of truth for navigation with guardrails against configuration drift.***
