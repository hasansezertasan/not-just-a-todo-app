# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""HTML snapshot regression tests via syrupy.

Refresh baselines after intentional markup changes:

    pytest --snapshot-update tests/test_html_snapshots.py
"""

from typing import TYPE_CHECKING

import pytest

from tests.extensions import HTMLExtension

if TYPE_CHECKING:
    from flask.testing import FlaskClient
    from syrupy.assertion import SnapshotAssertion

PAGES = [
    ("index", "/"),
    ("about", "/about/"),
    ("login", "/login/"),
    ("register", "/register/"),
]


@pytest.mark.parametrize(("name", "path"), PAGES)
def test_page_html_snapshot(
    client: FlaskClient,
    snapshot: SnapshotAssertion,
    name: str,
    path: str,
) -> None:
    resp = client.get(path, follow_redirects=True)
    assert resp.status_code == 200
    assert resp.data == snapshot(extension_class=HTMLExtension, name=name)
