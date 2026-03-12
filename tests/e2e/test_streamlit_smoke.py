from __future__ import annotations

import pytest


@pytest.mark.e2e
def test_app_module_imports() -> None:
    """
    Minimal smoke test: importing the Streamlit app module should succeed.

    This catches import-time errors (missing dependencies, bad relative
    imports, etc.) without starting a real Streamlit server, which can be
    flaky in headless CI environments.
    """
    __import__("src.app")
