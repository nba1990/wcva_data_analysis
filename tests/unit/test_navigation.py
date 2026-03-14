from __future__ import annotations

import ast
from pathlib import Path

from src.navigation import (
    NAV_ITEMS,
    get_default_page,
    get_nav_item_ids,
)


def test_nav_item_ids_are_unique() -> None:
    ids = [item.id for item in NAV_ITEMS]
    assert len(ids) == len(set(ids)), "NAV_ITEMS ids must be unique"


def test_get_default_page_returns_first_nav_id() -> None:
    assert get_default_page() == NAV_ITEMS[0].id
    assert get_default_page() in get_nav_item_ids()


def test_get_nav_item_ids_order_and_custom_items() -> None:
    ids = get_nav_item_ids()
    assert ids == [item.id for item in NAV_ITEMS]
    # Custom iterable
    from src.navigation import NavItem

    custom = [NavItem(id="A", label="A", subtitle=None, icon=None)]
    assert get_nav_item_ids(custom) == ["A"]


def test_nav_item_ids_are_wired_in_app_dispatch() -> None:
    """
    Ensure every NavItem.id is handled in src/app.py page dispatch.

    This is a lightweight guard so new pages are not forgotten in the
    main app routing.
    """
    app_path = Path(__file__).resolve().parents[2] / "src" / "app.py"
    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    handled_ids: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) or isinstance(node, ast.IfExp):
            # Look for patterns like: if page == "Overview": ...
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "page"
            ):
                for comparator in test.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(
                        comparator.value, str
                    ):
                        handled_ids.add(comparator.value)

    nav_ids = set(get_nav_item_ids())

    # Every NavItem.id should appear in the dispatch block.
    missing = sorted(nav_ids - handled_ids)
    assert not missing, f"Navigation IDs missing from app.py dispatch: {missing}"


def test_nav_items_have_labels_and_subtitles() -> None:
    """
    Sanity‑check that primary navigation items are not empty.
    """
    for item in NAV_ITEMS:
        assert item.label.strip(), f"NavItem {item.id!r} must have a label"
        # subtitle is optional, but if present it should not be empty whitespace
        if item.subtitle is not None:
            assert item.subtitle.strip(), f"NavItem {item.id!r} has empty subtitle"


def test_deployment_health_page_is_present_in_navigation() -> None:
    ids = get_nav_item_ids()
    assert "Deployment Health" in ids
