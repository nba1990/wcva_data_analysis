# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

from pathlib import Path

from importlinter.application.use_cases import read_user_options
from importlinter.configuration import configure

REPO_ROOT = Path(__file__).resolve().parents[2]

configure()


def test_import_linter_config_loads_declared_contracts() -> None:
    """
    Guard against silent contract disablement caused by stale section naming.
    """
    options = read_user_options(config_filename=str(REPO_ROOT / ".importlinter"))

    assert len(options.contracts_options) == 2
    assert {contract["id"] for contract in options.contracts_options} == {
        "section_pages_not_cross_importing",
        "section_pages_dependency_direction",
    }


def test_import_linter_contracts_have_expected_types() -> None:
    options = read_user_options(config_filename=str(REPO_ROOT / ".importlinter"))
    contracts_by_id = {
        contract["id"]: contract for contract in options.contracts_options
    }

    assert (
        contracts_by_id["section_pages_not_cross_importing"]["type"] == "independence"
    )
    assert contracts_by_id["section_pages_dependency_direction"]["type"] == "layers"
