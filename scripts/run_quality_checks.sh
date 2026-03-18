#!/usr/bin/env bash

# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MODE="full"

usage() {
    cat <<'EOF'
Usage: scripts/run_quality_checks.sh [--quick] [--full]

Run the repository quality gates from the project root using .venv.

Modes:
  --full   Run the broader local validation suite (default):
           Ruff, import-linter, mypy, non-e2e tests with coverage,
           e2e smoke test, security scans, packaging, diagrams, and Sphinx docs.
           Note: pip-audit needs outbound network access to query vulnerability data.
  --quick  Run the faster day-to-day checks:
           Ruff, import-linter, mypy, and non-e2e tests with coverage.
EOF
}

while (($# > 0)); do
    case "$1" in
        --quick)
            MODE="quick"
            ;;
        --full)
            MODE="full"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if [[ ! -d "${REPO_ROOT}/.venv" ]]; then
    echo "Expected virtual environment at ${REPO_ROOT}/.venv" >&2
    echo "Create it first with: python -m venv .venv" >&2
    exit 1
fi

cd "${REPO_ROOT}"
source .venv/bin/activate

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        echo "Install the project dependencies in .venv before running this script." >&2
        exit 1
    fi
}

run_step() {
    local label="$1"
    shift

    printf '\n==> %s\n' "${label}"
    "$@"
}

require_command python
require_command pytest
require_command ruff
require_command lint-imports
require_command mypy

run_step "Ruff lint" ruff check .
run_step "Ruff format check" ruff format --check .
run_step "Import-linter contracts" lint-imports
run_step "mypy" mypy src/ tests/ --config-file pyproject.toml
run_step \
    "Pytest (non-e2e, with coverage)" \
    pytest tests/ -v --tb=short -x -m "not e2e" --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=57

if [[ "${MODE}" == "full" ]]; then
    require_command pip-audit
    require_command bandit
    require_command detect-secrets-hook
    require_command sphinx-build

    run_step "Pytest e2e smoke" pytest tests/e2e/test_streamlit_smoke.py -v --tb=short
    run_step "pip-audit" env XDG_CACHE_HOME=/tmp pip-audit
    run_step "Bandit" bandit -q -r src references/SROI_Wales_Voluntary_Sector/scripts tools
    run_step \
        "detect-secrets" \
        bash -lc 'git ls-files -z | xargs -0 detect-secrets-hook --baseline .secrets.baseline'
    run_step "Package build" python -m build --sdist --wheel --no-isolation
    run_step "Generate diagrams" python scripts/generate_diagrams.py
    run_step "Sphinx docs build" sphinx-build -b html docs/source docs/build/html
fi

printf '\nAll %s quality checks completed successfully.\n' "${MODE}"
