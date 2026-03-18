---
title: Architecture contracts
---

# Architecture contracts

This project encodes a small set of **import-time architecture rules** using `import-linter`. These contracts help keep the layering you see in the diagrams enforceable over time.

Currently enforced contracts:

1. **Section pages do not import each other directly**

   - **Contract**: ``[importlinter:section_pages_not_cross_importing]`` (type ``independence``).
   - **Intent**: Each module under :mod:`src.section_pages` should depend on shared helpers (config, navigation, analysis, charts) rather than reaching into other pages.
   - **Effect**: You can safely modify or move a page without creating hidden cycles via cross-imports.

2. **Section pages depend only “inwards” on shared helper layers**

   - **Contract**: ``[importlinter:section_pages_dependency_direction]`` (type ``layers``).
   - **Layers**:
     - ``src.section_pages``
     - ``src.page_context``, ``src.wave_context``, ``src.eda``
     - ``src.charts``, ``src.sroi_charts``, ``src.filters``, ``src.data_loader``, ``src.navigation``, ``src.wave_schema``
     - ``src.config``
   - **Intent**: Section pages sit at the **edge** of the system and may depend on shared page context, analysis, charting, filtering, schema, navigation, and configuration helpers.
   - **Scope note**: This contract is intentionally scoped to the reusable helper modules consumed by pages. The Streamlit entry point (:mod:`src.app`) imports pages to dispatch them, so it is deliberately outside this particular layered rule.
   - **Why this shape matters**: The current `import-linter` release used by the project expects contract sections to be named ``[importlinter:...]``. Older-looking ``[contract:...]`` sections are silently ignored, which can lead to the misleading summary ``Contracts: 0 kept, 0 broken`` even when the graph itself is analysed successfully.

## Running the contracts locally

Inside your virtualenv, run:

```bash
lint-imports
```

This reads ``.importlinter`` at the repository root and should currently report two active contracts. If you ever see ``Contracts: 0 kept, 0 broken``, treat that as a configuration problem rather than a passing architecture check.

## How this relates to the diagrams

- The **module dependency** diagrams (:doc:`module_dependencies`) show import relationships visually.
- The **class hierarchy** diagrams (:doc:`class_hierarchy`) highlight key dataclasses and context models.
- These **contracts** turn those conceptual layers into *enforced rules*, so future changes don’t accidentally blur the boundaries between:
  - shared configuration/runtime helpers,
  - analysis and charting helpers, and
  - section-page UI modules.
