from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_script_module():
    script_path = (
        Path(__file__).resolve().parents[2] / "tools" / "apply_license_headers.py"
    )
    spec = importlib.util.spec_from_file_location("apply_license_headers", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_strip_legacy_markdown_license_removes_visible_header_and_footer() -> None:
    module = _load_script_module()
    legacy_text = """# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

# Example Title

Body paragraph.

Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
"""

    cleaned = module.strip_legacy_markdown_license(legacy_text)

    assert cleaned == "# Example Title\n\nBody paragraph.\n"


def test_build_header_lines_uses_hidden_comment_block_for_markdown() -> None:
    module = _load_script_module()

    header = module.build_header_lines("markdown")

    assert header[:2] == [
        "<!--",
        "Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/",
    ]
    assert "SPDX-License-Identifier: AGPL-3.0-or-later" in header
    assert header[-2:] == ["-->", ""]


def test_strip_legacy_rst_license_removes_visible_header_and_footer() -> None:
    module = _load_script_module()
    legacy_text = """# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

Title
=====

Body paragraph.

Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
"""

    cleaned = module.strip_legacy_rst_license(legacy_text)

    assert cleaned == "Title\n=====\n\nBody paragraph.\n"


def test_build_header_lines_uses_rst_comment_block_for_rst() -> None:
    module = _load_script_module()

    header = module.build_header_lines("rst")

    assert header[0] == ".."
    assert "SPDX-License-Identifier: AGPL-3.0-or-later" in header[2]
    assert header[-1] == ""
