#!/usr/bin/env python

"""
Utility script to (re)apply standard AGPLv3 license notices across the
repository in an idempotent way.

Usage (from repo root):

    python tools/apply_license_headers.py

The script:
- Enumerates tracked files with `git ls-files`.
- Skips obvious binary/data formats (images, PDFs, archives, large CSVs, etc.).
- Inserts the standard copyright notice:
  - As `#` comments for code/config files (.py, .sh, .yml, .toml, etc.).
  - As a hidden HTML comment block for Markdown files.
  - As a hidden comment block for reStructuredText files.
  - As plain text for other text-only docs.
- Preserves Python shebang lines by inserting the header immediately after.
- Normalises older visible Markdown headers/footers into the current format.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

HASH_HEADER_LINES = [
    "# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/ ",
    "#",
    "# This program is free software: you can redistribute it and/or modify",
    "# it under the terms of the GNU Affero General Public License v3.",
    "#",
    "# See the LICENSE file for details.",
    "",
]

MARKDOWN_HEADER_LINES = [
    "<!--",
    "Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/",
    "SPDX-License-Identifier: AGPL-3.0-or-later",
    "See the LICENSE file for full licensing terms.",
    "-->",
    "",
]

RST_HEADER_LINES = [
    "..",
    "   Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/",
    "   SPDX-License-Identifier: AGPL-3.0-or-later",
    "   See the LICENSE file for full licensing terms.",
    "",
]

PLAIN_TEXT_HEADER_LINES = [
    "Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/",
    "",
    "This project is licensed under the GNU Affero General Public License v3.0",
    "(AGPLv3). See the LICENSE file for details.",
    "",
]

FOOTER_LINE = (
    "Source code available under AGPLv3: "
    "https://github.com/nba1990/wcva_data_analysis "
)

# Extensions treated as code/config where `#` comments are safe.
HASH_COMMENT_EXTS = {
    ".py",
    ".pyi",
    ".sh",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
}

# Plain-text/doc formats.
PLAIN_TEXT_EXTS = {
    ".rst",
    "",
}

HASH_COMMENT_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "requirements.txt",
    "requirements-docs.txt",
}

BAT_COMMENT_FILENAMES = {
    "make.bat",
}

SKIP_FILENAMES = {
    "LICENSE",
}


def is_binary(path: Path) -> bool:
    """Return True for obvious binary / data formats we should not edit."""
    bin_exts = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ods",
        ".bin",
        ".ico",
        ".mm",
        ".mp4",
        ".gz",
        ".zip",
        ".tar",
        ".bz2",
        ".xz",
        ".json",
        ".html",
        ".css",
        ".csv",
    }
    return path.suffix.lower() in bin_exts


def classify_file(rel_path: str, path: Path) -> str:
    """Return 'hash', 'markdown', 'rst', 'plain', 'bat', or 'skip' for the given file."""
    if path.name in SKIP_FILENAMES:
        return "skip"
    if is_binary(path):
        return "skip"

    ext = path.suffix.lower()

    if path.name in BAT_COMMENT_FILENAMES:
        return "bat"
    if path.name in HASH_COMMENT_FILENAMES:
        return "hash"
    if ext in HASH_COMMENT_EXTS or rel_path.startswith("."):
        return "hash"
    if ext == ".md":
        return "markdown"
    if ext == ".rst":
        return "rst"
    if ext in PLAIN_TEXT_EXTS:
        return "plain"

    # Default to hash-style comments for other small text files.
    return "hash"


def has_license_markers(lines: list[str]) -> bool:
    """Check whether a recognizable license notice already exists."""
    return any("Copyright (C) 2026 - Bharadwaj Raman" in line for line in lines) or any(
        "SPDX-License-Identifier: AGPL-3.0-or-later" in line for line in lines
    )


def strip_legacy_markdown_license(text: str) -> str:
    """Remove older visible Markdown license text before reapplying."""
    lines = text.splitlines()
    start = 0

    legacy_prefixes = {
        "# Copyright (C) 2026 - Bharadwaj Raman",
        "Copyright (C) 2026 - Bharadwaj Raman",
        "# This program is free software",
        "This project is licensed under the GNU Affero General Public License",
        "# it under the terms of the GNU Affero General Public License v3.",
        "# See the LICENSE file for details.",
        "SPDX-License-Identifier: AGPL-3.0-or-later",
        "See the LICENSE file for full licensing terms.",
    }
    legacy_exact_lines = {"#", "<!--", "-->"}

    while start < len(lines):
        line = lines[start].strip()
        if not line:
            start += 1
            continue
        if line in legacy_exact_lines:
            start += 1
            continue
        if any(line.startswith(prefix) for prefix in legacy_prefixes):
            start += 1
            continue
        break

    end = len(lines)
    while end > start and not lines[end - 1].strip():
        end -= 1

    if end > start and lines[end - 1].strip().startswith(
        "Source code available under AGPLv3"
    ):
        end -= 1

    while end > start and not lines[end - 1].strip():
        end -= 1

    cleaned_lines = lines[start:end]
    if not cleaned_lines:
        return ""
    return "\n".join(cleaned_lines) + "\n"


def strip_legacy_rst_license(text: str) -> str:
    """Remove older visible RST license text before reapplying."""
    lines = text.splitlines()
    start = 0

    legacy_prefixes = {
        "# Copyright (C) 2026 - Bharadwaj Raman",
        "Copyright (C) 2026 - Bharadwaj Raman",
        "# This program is free software",
        "This project is licensed under the GNU Affero General Public License",
        "# it under the terms of the GNU Affero General Public License v3.",
        "# See the LICENSE file for details.",
        "SPDX-License-Identifier: AGPL-3.0-or-later",
        "See the LICENSE file for full licensing terms.",
        "..",
        "Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/",
    }
    legacy_exact_lines = {"#"}

    while start < len(lines):
        line = lines[start].strip()
        if not line:
            start += 1
            continue
        if line in legacy_exact_lines:
            start += 1
            continue
        if line.startswith("Source code available under AGPLv3"):
            start += 1
            continue
        if any(line.startswith(prefix) for prefix in legacy_prefixes):
            start += 1
            continue
        break

    end = len(lines)
    while end > start and not lines[end - 1].strip():
        end -= 1

    if end > start and lines[end - 1].strip().startswith(
        "Source code available under AGPLv3"
    ):
        end -= 1

    while end > start and not lines[end - 1].strip():
        end -= 1

    cleaned_lines = lines[start:end]
    if not cleaned_lines:
        return ""
    return "\n".join(cleaned_lines) + "\n"


def build_header_lines(mode: str) -> list[str]:
    """Return the header block for the given file mode."""
    if mode == "hash":
        return HASH_HEADER_LINES.copy()
    if mode == "bat":
        result: list[str] = []
        for line in HASH_HEADER_LINES:
            if line.startswith("# "):
                result.append("REM " + line[2:])
            elif line == "#":
                result.append("REM")
            else:
                result.append(line)
        return result
    if mode == "markdown":
        return MARKDOWN_HEADER_LINES.copy()
    if mode == "rst":
        return RST_HEADER_LINES.copy()
    return PLAIN_TEXT_HEADER_LINES.copy()


def apply_to_file(rel_path: str) -> None:
    path = REPO_ROOT / rel_path
    if not path.is_file():
        return

    mode = classify_file(rel_path, path)
    if mode == "skip":
        return

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return

    if mode == "markdown":
        text = strip_legacy_markdown_license(text)
    elif mode == "rst":
        text = strip_legacy_rst_license(text)

    lines = text.splitlines()
    if has_license_markers(lines):
        return

    ext = path.suffix.lower()
    new_lines: list[str] = []

    # Preserve Python shebang lines at the very top.
    shebang_lines: list[str] = []
    idx = 0
    if ext == ".py" and lines:
        while idx < len(lines) and lines[idx].startswith("#!"):
            shebang_lines.append(lines[idx])
            idx += 1

    if shebang_lines:
        new_lines.extend(shebang_lines)

    # Header.
    new_lines.extend(build_header_lines(mode))

    # Rest of file (skip any shebang lines already copied).
    if shebang_lines:
        new_lines.extend(lines[idx:])
    else:
        new_lines.extend(lines)

    # Footer (skip Markdown so docs stay visually clean).
    if mode not in {"markdown", "rst"} and not any(
        "Source code available under AGPLv3" in line for line in new_lines
    ):
        if mode == "hash":
            new_lines.append(f"# {FOOTER_LINE}")
        elif mode == "bat":
            new_lines.append(f"REM {FOOTER_LINE}")
        else:
            new_lines.append(FOOTER_LINE)

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main() -> None:
    result = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    files = [line.strip() for line in result.splitlines() if line.strip()]

    for rel in files:
        apply_to_file(rel)


if __name__ == "__main__":
    main()
