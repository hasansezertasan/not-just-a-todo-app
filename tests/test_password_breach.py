# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Password-breach service tests — all network calls mocked."""

import hashlib
from typing import TYPE_CHECKING
from urllib.error import URLError

from app.services import password_breach as breach_service

if TYPE_CHECKING:
    from flask import Flask
    from pytest_mock import MockerFixture


def _hibp_response_for(password: str, count: int) -> str:
    """Build a fake HIBP body containing the suffix for `password`."""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()  # noqa: S324
    suffix = sha1[5:]
    return f"OTHERSUFFIX:1\n{suffix}:{count}\n"


def _stub_urlopen(body: str):
    """Return an object behaving like urlopen()'s context-manager response."""

    class _Resp:
        def read(self) -> bytes:
            return body.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    return _Resp()


def test_feature_flag_off_skips_check(app: Flask, mocker: MockerFixture) -> None:
    spy = mocker.patch("app.services.password_breach.urlopen")
    with app.app_context():
        # Reset flag — `app` fixture is session-scoped, prior tests mutate it.
        app.config["PASSWORD_BREACH_CHECK_ENABLED"] = False
        assert breach_service.is_breached("password") is False
    spy.assert_not_called()


def test_breached_password_returns_true(app: Flask, mocker: MockerFixture) -> None:
    mocker.patch(
        "app.services.password_breach.urlopen",
        return_value=_stub_urlopen(_hibp_response_for("hunter2", count=42)),
    )
    with app.app_context():
        app.config["PASSWORD_BREACH_CHECK_ENABLED"] = True
        assert breach_service.is_breached("hunter2") is True


def test_clean_password_returns_false(app: Flask, mocker: MockerFixture) -> None:
    mocker.patch(
        "app.services.password_breach.urlopen",
        return_value=_stub_urlopen("OTHERSUFFIX:1\n"),
    )
    with app.app_context():
        app.config["PASSWORD_BREACH_CHECK_ENABLED"] = True
        assert breach_service.is_breached("strong-novel-password") is False


def test_api_failure_fails_open(app: Flask, mocker: MockerFixture) -> None:
    """Network error → return False so registration isn't blocked by HIBP outage."""
    mocker.patch(
        "app.services.password_breach.urlopen",
        side_effect=URLError("connection refused"),
    )
    with app.app_context():
        app.config["PASSWORD_BREACH_CHECK_ENABLED"] = True
        assert breach_service.is_breached("anything") is False


def test_breach_count_returns_none_on_failure(
    app: Flask, mocker: MockerFixture
) -> None:
    mocker.patch(
        "app.services.password_breach.urlopen",
        side_effect=TimeoutError("slow"),
    )
    with app.app_context():
        assert breach_service.breach_count("anything", timeout=0.1) is None
