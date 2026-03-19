# Project overrides (Codex)

This file overrides or extends the global rules in `~/.codex/AGENTS.md`. Codex gives precedence to the file closest to the working directory, so anything below applies in this repo in addition to (or in place of) the global rules.

## Project-specific overrides

- **Conventions:** Follow this repo’s **CONTRIBUTING.md**, ADRs, and architecture docs. Prefer existing patterns in `src/`, `tests/`, and `docs/`.
- **Environment:** Use the project virtual environment at **`.venv`** in the repo root for all Python commands (tests, lint, format, docs, scripts).
- **Documentation:** When changing behaviour or structure, update the relevant docs under `docs/` and any architecture notes as part of the same change.
- **Commits:** Use the commit message templates under `docs/git/templates/` (for example, `git_commit_message_general_template.md` and `git_commit_message_templates.md`). Follow the `<type>(<scope>): <summary in imperative mood>` format and the documented commit types (such as `feat`, `fix`, `docs`, `refactor`, `test`, `chore`).

Add or edit only the overrides you need for this project; the global rules apply for everything else.
