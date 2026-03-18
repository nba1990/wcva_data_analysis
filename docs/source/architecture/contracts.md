---
title: Architecture contracts
---

# Architecture contracts

This project encodes a small set of **import-time architecture rules** using `import-linter`. These contracts help keep the layering you see in the diagrams enforceable over time.

Currently enforced contracts:

1. **Section pages do not import each other directly**

   - **Contract**: ``[contract:section_pages_not_cross_importing]`` (type ``independence``).
   - **Intent**: Each module under :mod:`src.section_pages` should depend on shared helpers (config, navigation, analysis, charts) rather than reaching into other pages.
   - **Effect**: You can safely modify or move a page without creating hidden cycles via cross-imports.

2. **Section pages depend only “inwards” on core and analysis layers**

   - **Contract**: ``[contract:section_pages_dependency_direction]`` (type ``layers``).
   - **Layers**:
     - ``config_and_core`` → :mod:`src.config`, :mod:`src.navigation`, :mod:`src.app`, :mod:`src.wave_context`
     - ``analysis_and_charts`` → :mod:`src.data_loader`, :mod:`src.eda`, :mod:`src.charts`, :mod:`src.sroi_charts`
     - ``pages`` → :mod:`src.section_pages`
   - **Intent**: Section pages sit at the **edge** of the system and are allowed to depend on configuration, analysis, and chart helpers—but not the other way around.

## Running the contracts locally

Inside your virtualenv, run:

```bash
lint-imports
```

This will read ``.importlinter`` at the repo root and fail if any contract is violated.

## How this relates to the diagrams

- The **module dependency** diagrams (:doc:`module_dependencies`) show import relationships visually.
- The **class hierarchy** diagrams (:doc:`class_hierarchy`) highlight key dataclasses and context models.
- These **contracts** turn those conceptual layers into *enforced rules*, so future changes don’t accidentally blur the boundaries between:
  - core configuration/runtime,
  - analysis and charting helpers, and
  - section-page UI modules.
