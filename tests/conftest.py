# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>

import os
import socket
import threading

import pytest

os.environ.setdefault("SQLALCHEMY_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET_KEY", "test-secret")

from collections.abc import Iterator

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.serving import make_server

from app.app import app as flask_app  # noqa: E402
from app.db.models.base import db as _db  # noqa: E402
from app.db.models.users import User  # noqa: E402


@pytest.fixture(scope="session")
def app() -> Flask:
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    return flask_app


@pytest.fixture
def db(app: Flask) -> Iterator[object]:
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app: Flask, db: object) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def user(db: object) -> User:
    u = User(
        username="alice",
        hashed_password="s3cret-pw",
        first_name="Alice",
        last_name="Anderson",
        email="alice@example.com",
    )
    u.upsert()
    return u


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def live_server(app: Flask, db: object) -> Iterator[str]:
    port = _free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
