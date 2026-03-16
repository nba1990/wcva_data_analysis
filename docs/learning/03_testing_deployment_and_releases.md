<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Testing, Deployment, and Releases in This Repo

This guide focuses on the practical engineering workflow around the app rather
than on the survey analysis itself.

## Testing layers

- unit tests: pure logic in config, loaders, charts, EDA, narratives
- integration tests: cross-module behaviour such as wave trends
- e2e smoke tests: import/boot checks for the Streamlit app

The sample fixture is important because it lets CI and documentation import the
app without private data.

## Deployment mindset

The app now includes a `Deployment Health` page so hosted failures become easier
to diagnose. This is a useful pattern for small internal/public data apps:

- fail clearly
- expose resolved runtime sources
- distinguish required vs optional assets
- provide next-step guidance in the app itself

## Git hygiene lessons

This repo already went through:

- removing private data from tracked files
- rewriting git history with `git filter-repo`
- force-pushing cleaned branches and tags
- documenting the process in `docs/HISTORY_REWRITE_AND_STREAMLIT_SECRETS.md`

That is not a normal daily workflow, but it is worth understanding if you work
in public repos with sensitive data nearby.

## Release flow used here

The lightweight release pattern in this repo is:

1. update docs and changelog
2. run tests
3. commit the release-prep changes
4. create an annotated tag
5. push branches and tags
6. publish a GitHub release

This is intentionally simple, but it is enough to teach:

- version discipline
- release notes
- tag alignment
- patch releases for CI/deployment fixes
