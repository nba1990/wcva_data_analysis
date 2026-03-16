#!/usr/bin/env python

"""
Utility script to (re)apply standard AGPLv3 license headers and footers
across the repository in an idempotent way.

Usage (from repo root):

    python tools/apply_license_headers.py

The script:
- Enumerates tracked files with `git ls-files`.
- Skips obvious binary/data formats (images, PDFs, archives, large CSVs, etc.).
- Inserts the standard copyright header and AGPLv3 footer:
  - As `#` comments for code/config files (.py, .sh, .yml, .toml, etc.).
  - As plain text blocks for Markdown, RST, and other text docs.
- Preserves Python shebang lines by inserting the header immediately after.
- Avoids duplicating the header/footer if they are already present.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

HEADER_LINES = [
    "# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/ ",
    "#",
    "# This program is free software: you can redistribute it and/or modify",
    "# it under the terms of the GNU Affero General Public License v3.",
    "#",
    "# See the LICENSE file for details.",
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

# Plain-text/doc formats (header/footer inserted as-is).
PLAIN_TEXT_EXTS = {
    ".md",
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
    """Return 'hash', 'plain', 'bat', or 'skip' for the given file."""
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
    if ext in PLAIN_TEXT_EXTS:
        return "plain"

    # Default to hash-style comments for other small text files.
    return "hash"


def has_license_markers(lines: list[str]) -> bool:
    """Check whether both header and footer markers already exist."""
    has_header = any("Copyright (C) 2026 - Bharadwaj Raman" in line for line in lines)
    has_footer = any("Source code available under AGPLv3" in line for line in lines)
    return has_header and has_footer


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
    if mode == "hash":
        # Use hash comments for header/footer.
        for hl in HEADER_LINES:
            if hl:
                new_lines.append(hl)
            else:
                new_lines.append("")
    elif mode == "bat":
        for hl in HEADER_LINES:
            if hl.startswith("# "):
                new_lines.append("REM " + hl[2:])
            elif hl == "#":
                new_lines.append("REM")
            else:
                new_lines.append(hl)
    else:  # "plain"
        new_lines.extend(HEADER_LINES)

    # Rest of file (skip any shebang lines already copied).
    if shebang_lines:
        new_lines.extend(lines[idx:])
    else:
        new_lines.extend(lines)

    # Footer (skip if already present in the new lines).
    if not any("Source code available under AGPLv3" in line for line in new_lines):
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
