# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Smoke tests — verify the app boots and exposes its operational endpoints."""

from typing import TYPE_CHECKING

from flask import Flask

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_app_boots(app: Flask) -> None:
    assert isinstance(app, Flask)
    assert app.config["TESTING"] is True


def test_required_config_keys_present(app: Flask) -> None:
    required = {
        "SECRET_KEY",
        "SQLALCHEMY_DATABASE_URI",
        "PERMANENT_SESSION_LIFETIME",
        "SESSION_COOKIE_HTTPONLY",
        "SESSION_COOKIE_SECURE",
        "SESSION_COOKIE_SAMESITE",
        "PREFERRED_URL_SCHEME",
    }
    assert required <= set(app.config.keys())


def test_healthz_returns_ok(client: FlaskClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_healthz_no_auth_required(app: Flask) -> None:
    """Health endpoint must be reachable without a session.

    Orchestrators (Docker, k8s, load balancers) probe it without logging in.
    """
    client = app.test_client()
    response = client.get("/healthz")
    assert response.status_code == 200


def test_seed_fixtures_ship_with_package() -> None:
    """Fixtures must ship inside the package so containers can run seed commands."""
    from app.config import FIXTURES_DIR

    assert (FIXTURES_DIR / "users.json").is_file()
    assert (FIXTURES_DIR / "sequences.json").is_file()


def test_migrations_dir_ships_with_package() -> None:
    from pathlib import Path

    import app

    migrations_dir = Path(app.__file__).parent / "db" / "migrations"
    assert (migrations_dir / "alembic.ini").is_file()
    assert (migrations_dir / "env.py").is_file()
