# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""HMAC-signed token service tests."""

import time
from typing import TYPE_CHECKING

import pytest

from app.services import tokens as token_service
from app.services.tokens import TokenError

if TYPE_CHECKING:
    from flask import Flask


def test_sign_and_verify_roundtrip(app: Flask) -> None:
    with app.app_context():
        token = token_service.sign({"user_id": 42}, salt="password-reset")
        payload = token_service.verify(
            token, salt="password-reset", max_age_seconds=60
        )
    assert payload == {"user_id": 42}


def test_tampered_token_rejected(app: Flask) -> None:
    with app.app_context():
        token = token_service.sign(7, salt="password-reset")
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(TokenError, match="invalid"):
            token_service.verify(
                tampered, salt="password-reset", max_age_seconds=60
            )


def test_cross_salt_token_rejected(app: Flask) -> None:
    """A token issued for one flow must not validate against another."""
    with app.app_context():
        token = token_service.sign(99, salt="password-reset")
        with pytest.raises(TokenError, match="invalid"):
            token_service.verify(
                token, salt="email-verify", max_age_seconds=60
            )


def test_expired_token_rejected(app: Flask) -> None:
    """Tokens past `max_age_seconds` raise expiry, not invalid-sig.

    itsdangerous timestamps at ~1s granularity, so we sleep past 2s and
    set `max_age_seconds=1` to guarantee the elapsed-vs-max comparison
    triggers regardless of subsecond rounding.
    """
    with app.app_context():
        token = token_service.sign(1, salt="password-reset")
        time.sleep(2.1)
        with pytest.raises(TokenError, match="expired"):
            token_service.verify(
                token, salt="password-reset", max_age_seconds=1
            )
