# ADR-004 – Multi-user state and caching strategy

## Context

The dashboard is deployed to environments such as Streamlit Community Cloud, where multiple users may interact with the app concurrently. Each user may:

- Apply different filters (organisation size, scope, activity, concerns).
- Adjust accessibility settings (text scale, colour-blind friendly palette).
- Navigate between pages independently.

Streamlit’s architecture provides **per-session isolation** (each browser tab gets its own session and `st.session_state`), but backend design choices can still accidentally cause **cross-user contamination** if mutable globals or shared caches are misused.

The app also needs to:

- Avoid re-reading and re-processing the dataset for every interaction and every user.
- Maintain a clear separation between per-user UI state and shared, read-only data.

## Decision

We adopted the following multi-user and caching strategy:

- **Per-user/session state**:
  - Filters, accessibility preferences, and current page are stored in `st.session_state`:
    - `st.session_state["current_page"]` for navigation.
    - `st.session_state["app_ui_config"]` for the UI config dataclass (text size mode, `text_scale`, `palette_mode`, filter options, selected values, suppression flag). The app uses a single `StreamlitAppUISharedConfigState` instance per session, created and retrieved via `get_app_ui_config()` in `src.config`. The dataclass is defined in a separate module; the instance is stored under a key in session state, not as a module-level global.
  - This state is set on each rerun for the current session and is not shared between sessions.
- **Shared data and resources**:
  - The Wave 2 dataset is loaded once per process via `@st.cache_data` (`get_data()` in `app.py`), so all sessions reuse the same in-memory DataFrame.
  - Any future heavy resources (e.g. models, external connections) should be wrapped in `st.cache_resource`.
- **Global configuration vs mutable globals**:
  - Module-level globals in `src/config.py` are used only for constants (palettes, response orderings, mapping dictionaries).
  - We avoid using mutable module-level collections for per-user data to prevent cross-user leaks.

## Consequences

- Each user sees **their own view** of the dashboard:
  - Changing filters or accessibility settings in one browser tab does not alter another user’s filters or text size.
  - The suppression logic (based on `K_ANON_THRESHOLD`) runs per session using that session’s filtered `n`.
- Shared caches improve performance:
  - All users benefit from cached data loading while still applying their own filters on top of the shared base DataFrame.
- The design encourages clear separation:
  - When adding new features, per-user settings should live in `st.session_state` (e.g. the per-session UI config instance from `get_app_ui_config()`).
  - New shared data loading or resource initialisation should use `st.cache_data` / `st.cache_resource` where appropriate.
- Documentation (in `ARCHITECTURE.md` and this ADR) gives future contributors a reference for **safe vs unsafe** patterns in a multi-user Streamlit app, reducing the risk of inadvertent global state bugs.
