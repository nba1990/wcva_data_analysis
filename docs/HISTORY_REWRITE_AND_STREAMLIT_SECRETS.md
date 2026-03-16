<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# History rewrite and Streamlit secrets runbook

This project previously tracked private files under `datasets/`. Removing them from the current branch is **not enough**; the Git history, tags, and remote refs must be rewritten and force-pushed.

## Scope to remove

Purge the entire historical `datasets/` directory, including:

- `datasets/WCVA_W2_Anonymised_Dataset.csv`
- `datasets/WCVA_W2_Anonymised_Dataset.ods`
- `datasets/Baromedr_Cymru_QA_Response_Options.docx`
- `datasets/Baromedr_Cymru_QA_Response_Options.pdf`
- `datasets/WCVA_W1_Context_Extracted.md`
- `datasets/la_context_wales.csv`

## Before you rewrite

1. Make sure teammates stop pushing to the repository until the rewrite is complete.
2. Confirm you have a local backup clone or mirror before running destructive history edits.
3. Ensure the working tree is clean.

## Local rewrite commands

Run these commands from a clean clone of the repository:

```bash
git branch backup/pre-filter-repo
git tag backup-pre-filter-repo
git filter-repo --force --sensitive-data-removal --invert-paths --path datasets/
grep '^refs/pull/.*/head$' .git/filter-repo/changed-refs || true
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Push rewritten history

Force-push every rewritten ref:

```bash
git push <remote> --force --all
git push <remote> --force --tags
```

Replace `<remote>` with your actual remote name. In this repository, `git remote -v` currently shows `GitHub-NBA1990-WCVA_DATA_ANALYSIS`.

If any old branches were deleted on the remote but still exist in local refs, remove them explicitly as needed.

## After the push

1. Ask GitHub Support to fully purge cached blobs only if the sensitive files remain accessible through cached URLs.
2. In GitHub, rotate any credentials that may have been exposed in history.
3. Ask collaborators to re-clone the repository or hard-reset to the new history.
4. Rebuild any releases, archives, or deployment artifacts that were produced from the old history.

## Streamlit Community Cloud setup

This repo now supports private runtime data through environment variables or Streamlit secrets:

- `WCVA_DATASET_PATH` or `dataset_path`
- `WCVA_DATASET_URL` or `dataset_url`
- `WCVA_LA_CONTEXT_PATH` or `la_context_path`
- `WCVA_LA_CONTEXT_URL` or `la_context_url`

For Community Cloud, the practical option is usually a **private URL** stored in secrets, because the hosted filesystem is ephemeral. A minimal `.streamlit/secrets.toml` equivalent is:

```toml
[wcva_data]
dataset_url = "https://example.com/private/wcva-wave2.csv"
```

The app will:

1. Try `WCVA_DATASET_PATH` / `dataset_path`.
2. Fall back to `WCVA_DATASET_URL` / `dataset_url`.
3. Fall back to a local untracked copy under `datasets/` if present.
4. Fall back to the bundled sample fixture and enter explicit **demo mode** if no real dataset source is available.
5. Use the checked-in public local-authority context file unless you override it.

## Demo mode behavior

If the app or `python -m src.generate_presentation` cannot resolve the real
Wave dataset, they do not fail immediately anymore. Instead they:

- load the bundled sample fixture from `tests/fixtures/`
- mark the session/output as **DEMO / SAMPLE DATA**
- expose the resolved runtime source in the in-app `Deployment Health` page
- write demo-labelled presentation outputs by default

This keeps docs builds, CI smoke tests, and first deployments working while
making it hard to mistake the fixture for the real release data.

## Local development after the rewrite

You can keep a private untracked copy at the old path:

```bash
mkdir -p datasets
cp /secure/location/WCVA_W2_Anonymised_Dataset.csv datasets/
```

Because `/datasets/` is now ignored, the file will stay out of Git while local development continues to work.
