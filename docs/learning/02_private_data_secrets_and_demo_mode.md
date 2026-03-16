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
