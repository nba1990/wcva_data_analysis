from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DOCS_AUTO_DIR = PROJECT_ROOT / "docs" / "source" / "architecture" / "auto"


def run(cmd: list[str]) -> None:
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"Command failed ({completed.returncode}): {' '.join(cmd)}")


def ensure_output_dir() -> None:
    DOCS_AUTO_DIR.mkdir(parents=True, exist_ok=True)


def generate_pydeps_graph() -> None:
    """
    Reserved for a future pydeps-based import graph.
    Currently unused in the docs to keep the pipeline simple and stable.
    """
    return None


def generate_pyreverse_graphs() -> None:
    """
    Generate class/package diagrams for selected subsystems using pyreverse.
    Outputs DOT files into the auto/ directory.
    """
    # High-level package overview for all of src/*
    run(
        [
            "pyreverse",
            "src",
            "-o",
            "dot",
            "-d",
            str(DOCS_AUTO_DIR),
        ]
    )

    # Focused view: navigation + section pages
    run(
        [
            "pyreverse",
            "src/navigation.py",
            "src/section_pages",
            "-o",
            "dot",
            "-p",
            "nav_pages",
            "-d",
            str(DOCS_AUTO_DIR),
        ]
    )

    # Focused view: analysis and data-loading layer
    run(
        [
            "pyreverse",
            "src/data_loader.py",
            "src/eda.py",
            "src/wave_context.py",
            "-o",
            "dot",
            "-p",
            "analysis_layer",
            "-d",
            str(DOCS_AUTO_DIR),
        ]
    )

    # Focused view: charting and SROI figures
    run(
        [
            "pyreverse",
            "src/charts.py",
            "src/sroi_charts",
            "-o",
            "dot",
            "-p",
            "charts_layer",
            "-d",
            str(DOCS_AUTO_DIR),
        ]
    )


def main() -> None:
    ensure_output_dir()
    generate_pydeps_graph()
    generate_pyreverse_graphs()


if __name__ == "__main__":
    main()
