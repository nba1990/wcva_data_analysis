---
title: Class hierarchy
---

# Class hierarchy

This page focuses on **key classes and datamodels** rather than every possible type in the codebase.

## Configuration & runtime data

```{inheritance-diagram} src.config
   :parts: 1
```

The `src.config` module defines dataclasses and configuration objects used across the app (UI config, palettes, k-anonymity thresholds, etc.).

## Navigation

```{inheritance-diagram} src.navigation.NavItem
   :parts: 1
```

`NavItem` instances define the sidebar navigation model (IDs, labels, icons) and are used by both `src/app.py` and `src/navigation.py`.

## Wave context

```{inheritance-diagram} src.wave_context
   :parts: 1
```

The `src.wave_context` module provides Pydantic models describing each survey wave, plus helpers for trend and comparison analysis.
