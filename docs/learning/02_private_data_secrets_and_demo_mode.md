<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Private Data, Secrets, and Demo Mode

This repository intentionally separates:

- public code and public reference material
- private survey datasets used at runtime
- safe sample fixtures used for tests, smoke checks, and documentation

## Runtime data model

For the main Wave dataset, the app now resolves data in this order:

1. `WCVA_DATASET_PATH`
2. `dataset_path` in Streamlit secrets
3. `WCVA_DATASET_URL`
4. `dataset_url` in Streamlit secrets
5. local untracked fallback in `datasets/`
6. bundled sample fixture in `tests/fixtures/` (demo mode)

For local-authority context, the default is the checked-in public file:

- `references/context/la_context_wales.csv`

You can still override it with path/URL env vars or matching Streamlit secrets.

## Why this matters

- private survey data should not live in a public git history
- deployment platforms often have ephemeral filesystems
- tests and docs still need a safe dataset so imports and smoke checks work

## Demo mode

If the real dataset is unavailable, the app and presentation generator fall back
to the bundled fixture dataset and mark themselves as demo/sample mode.

That gives you:

- safe docs builds
- safer first deploys
- easier smoke testing
- a working UI even before private data is configured

It should never be confused with the real Wave release. That is why demo mode
is deliberately noisy in the UI and output artefacts.

## Practical commands

Local private file:

```bash
export WCVA_DATASET_PATH=/secure/location/WCVA_W2_Anonymised_Dataset.csv
streamlit run src/app.py
```

Private URL:

```bash
export WCVA_DATASET_URL='https://example.com/private/wcva-wave2.csv'
python -m src.generate_presentation
```

Local fallback path:

```bash
mkdir -p datasets
cp /secure/location/WCVA_W2_Anonymised_Dataset.csv datasets/
```

Streamlit Community Cloud secrets:

```toml
[wcva_data]
dataset_url = "https://example.com/private/wcva-wave2.csv"
```

## Secrets and env hygiene checklist

Use this as a quick review before putting a deployment in front of real users:

- **Keep private data out of Git**:
  - Do not commit `datasets/WCVA_W2_Anonymised_Dataset.csv` or any other real survey extract.
  - If you have accidentally committed private data, rotate the dataset and rewrite history before making the repo public.
- **Use env vars / secrets for configuration**:
  - Prefer `WCVA_DATASET_PATH` / `WCVA_DATASET_URL` and Streamlit secrets (`[wcva_data]`) over hard-coding.
  - Store any API keys, database passwords, and presigned URLs in a secrets manager, not in `src/*.py`, `Dockerfile`, or `docker-compose.yml`.
- **Treat URLs as secrets**:
  - Private dataset URLs should normally be HTTPS and access-controlled (for example, presigned S3 or equivalent).
  - Avoid long-lived public HTTP URLs for real Wave datasets; the app will log a warning if you use non-HTTPS sources.
- **Rely on masking and avoid new leaks**:
  - Deployment Health and the logging shim intentionally mask runtime paths and URLs when displaying them.
  - When adding new log statements or diagnostics, use the existing helpers instead of printing raw paths or credentials.
- **Understand demo mode vs real mode**:
  - Demo mode is meant for documentation, smoke tests, and training; it uses the bundled fixture from `tests/fixtures/`.
  - Real analysis should only be done once `Deployment Health` reports a non-demo dataset source and all required assets present.

For container- and deployment-specific hardening tips (including reverse proxies and non-root users), see `docs/DOCKER_AND_DEPLOYMENT.md`.
