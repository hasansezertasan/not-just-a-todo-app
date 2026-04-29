# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Visual (PNG) snapshot regression tests via pytest-playwright + syrupy.

Refresh baselines after intentional UI changes:

    pytest --snapshot-update tests/test_visual_snapshots.py

Requires `playwright install chromium` once.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.extensions import PNGImageExtension

if TYPE_CHECKING:
    from playwright.sync_api import Page
    from syrupy.assertion import SnapshotAssertion

VIEWPORT = {"width": 1280, "height": 720}


PAGES = [
    ("index", "/"),
    ("about", "/about"),
]


CLICK_PAGES = [
    ("login", "Login"),
    ("register", "Register"),
]


@pytest.mark.parametrize(("name", "path"), PAGES)
def test_visual_snapshot_direct(
    live_server: str,
    page: Page,
    snapshot: SnapshotAssertion,
    name: str,
    path: str,
) -> None:
    page.set_viewport_size(VIEWPORT)
    page.goto(f"{live_server}{path}")
    page.wait_for_load_state("networkidle")
    png = page.screenshot(full_page=True)
    assert png == snapshot(extension_class=PNGImageExtension, name=name)


@pytest.mark.parametrize(("name", "link_text"), CLICK_PAGES)
def test_visual_snapshot_via_click(
    live_server: str,
    page: Page,
    snapshot: SnapshotAssertion,
    name: str,
    link_text: str,
) -> None:
    page.set_viewport_size(VIEWPORT)
    page.goto(f"{live_server}/")
    page.get_by_role("link", name=link_text).click()
    page.wait_for_load_state("networkidle")
    png = page.screenshot(full_page=True)
    assert png == snapshot(extension_class=PNGImageExtension, name=name)
