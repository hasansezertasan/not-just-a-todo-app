# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>

import socket
import threading
from typing import TYPE_CHECKING

import pytest
from werkzeug.serving import make_server

from app.config import Settings
from app.db.models.base import db as _db
from app.db.models.users import User
from app.factory import create_app

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flask import Flask
    from flask.testing import FlaskClient


@pytest.fixture(scope="session")
def app() -> Flask:
    settings = Settings(
        app_env="testing",
        sqlalchemy_database_url="sqlite:///:memory:",
        session_secret_key="test-secret",  # type: ignore[arg-type]
    )
    flask_app = create_app(settings)
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
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
