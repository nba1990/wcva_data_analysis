# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

from __future__ import annotations

from src.navigation import NAV_ITEMS, get_default_page, get_nav_item_ids


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
    Ensure every NavItem.id is handled in src.app.PAGE_RENDERERS.

    This guards against adding a navigation item without a matching page renderer.
    """
    import src.app as app_module

    nav_ids = set(get_nav_item_ids())
    handled_ids = set(app_module.PAGE_RENDERERS.keys())

    missing = sorted(nav_ids - handled_ids)
    assert not missing, f"Navigation IDs missing from PAGE_RENDERERS: {missing}"


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


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
