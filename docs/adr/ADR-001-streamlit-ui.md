<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# ADR-001 – Use Streamlit for the WCVA dashboard UI

## Context

The WCVA Baromedr Wave 2 project needed an interactive, data-heavy dashboard that:

- Could be developed quickly in Python, close to the analytical code.
- Would support rich charts, filters, and multi-page navigation.
- Could be deployed easily to a managed environment (e.g. Streamlit Community Cloud) for non-technical users.

Alternatives considered included:

- Building a custom frontend (React/Vue) with a separate API layer.
- Using a different Python web framework such as Dash or a full-stack framework like Django with custom JS.

## Decision

We chose **Streamlit** as the primary UI framework because:

- It allows writing the entire dashboard in Python, minimising context switches.
- It has built-in primitives for layout, forms, and caching, which map well to dashboard-style apps.
- The deployment story is straightforward via Streamlit Community Cloud.
- It is well-supported in the data-science ecosystem and works cleanly with Pandas, Plotly, and other libraries already in use.

## Consequences

- The app follows Streamlit’s **per-session rerun model**: on each interaction, the script executes top-to-bottom for that user session.
- We must pay attention to:
  - Avoiding mutable module-level globals for user-specific state.
  - Using `st.session_state` and small configuration objects for per-user preferences.
  - Using `st.cache_data` / `st.cache_resource` for shared, read-only data and heavy resources.
- Frontend customisation is constrained to what Streamlit supports via layout primitives, components, and limited CSS injection; fully bespoke UX would require more engineering or a different stack.
