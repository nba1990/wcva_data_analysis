<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# ADR-007: Runtime data resolution and explicit demo mode

- Status: Accepted
- Date: 2026-03-16

## Context

The repository now needs to remain public and production-usable without
tracking private Wave datasets in Git. At the same time, the Streamlit app,
documentation builds, smoke tests, and presentation generator must keep working
when the real dataset is not present on disk.

## Decision

- Resolve the primary Wave dataset from environment variables, Streamlit
  secrets, URL-based sources, or an untracked local fallback.
- Keep the local-authority context CSV publicly tracked under
  `references/context/`.
- Fall back to the bundled sample fixture when the real Wave dataset is not
  available.
- Mark that fallback explicitly as demo/sample mode in the app and
  presentation outputs.
- Keep the runtime-source resolution metadata visible through the in-app
  `Deployment Health` page.

## Consequences

- The app stays bootable in CI, docs builds, and first-deploy environments.
- Presentation generation no longer depends on a tracked private dataset.
- Demo/sample outputs become possible without pretending to be real releases.
- Runtime configuration becomes slightly more complex, but the behavior is more
  explicit and safer for public-repo use.
