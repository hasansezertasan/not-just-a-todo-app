# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""HMAC-signed, time-bounded tokens for sensitive URLs.

Wraps `itsdangerous.URLSafeTimedSerializer` with a per-purpose salt so
tokens issued for different flows (password-reset vs email-verify) can't
be cross-replayed. Backed by Flask's `SECRET_KEY` so signature validity
follows secret rotation automatically.

Designed for embed-in-URL use cases:

    https://example.com/reset/<token>

The token carries an opaque payload (typically a user_id) signed with
HMAC. Callers `verify(...)` to retrieve the payload AND assert the token
hasn't expired or been tampered with.

Compatible with future password-reset, email-verify, magic-login, and
unsubscribe flows.
"""

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class TokenError(Exception):
    """Raised when a token is invalid, expired, or tampered with."""


def _serializer(salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=current_app.config["SECRET_KEY"],
        salt=salt,
    )


def sign(payload: object, *, salt: str) -> str:
    """Return a URL-safe HMAC-signed token wrapping `payload`.

    `salt` namespaces the token to a specific flow — pick a unique
    constant per use case (e.g. `"password-reset"`, `"email-verify"`)
    so tokens minted for one flow can't be replayed against another.
    """
    return _serializer(salt).dumps(payload)


def verify(token: str, *, salt: str, max_age_seconds: int) -> object:
    """Validate `token` and return the embedded payload.

    Raises `TokenError` on signature mismatch, expiry, or any other
    malformed input. Caller decides whether to flash a generic message
    (recommended) or surface the specific failure mode.
    """
    serializer = _serializer(salt)
    try:
        return serializer.loads(token, max_age=max_age_seconds)
    except SignatureExpired as exc:
        msg = "token expired"
        raise TokenError(msg) from exc
    except BadSignature as exc:
        msg = "invalid token"
        raise TokenError(msg) from exc
