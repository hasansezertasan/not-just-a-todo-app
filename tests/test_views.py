# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_index_returns_200(client: FlaskClient) -> None:
    resp = client.get("/")
    assert resp.status_code in (200, 302)


def test_about_page(client: FlaskClient) -> None:
    resp = client.get("/about/", follow_redirects=True)
    assert resp.status_code == 200


def test_login_page(client: FlaskClient) -> None:
    resp = client.get("/login/", follow_redirects=True)
    assert resp.status_code == 200


def test_protected_route_redirects(client: FlaskClient) -> None:
    resp = client.get("/sequence/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login/" in resp.headers["Location"]
