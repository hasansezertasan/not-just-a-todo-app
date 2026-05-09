# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Account-lockout primitives.

Pairs with flask-limiter's per-IP rate limit. The IP limit slows brute-force
*attempts*; the per-account lockout slows credential-stuffing against a
specific username even when attempts come from rotating IPs.
"""

import datetime
from typing import TYPE_CHECKING

from flask import current_app

if TYPE_CHECKING:
    from app.db.models.users import User


def _now() -> datetime.datetime:
    """Naive UTC timestamp.

    SQLite stores datetimes without timezone metadata; mixing naive (DB)
    and aware (Python) values raises `TypeError` on comparison. Using
    naive UTC everywhere keeps the contract uniform across SQLite/MySQL/
    Postgres.
    """
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def is_locked(user: User) -> bool:
    """`True` if the user is currently locked out."""
    if user.locked_until is None:
        return False
    locked_until = user.locked_until
    if locked_until.tzinfo is not None:
        locked_until = locked_until.astimezone(datetime.UTC).replace(tzinfo=None)
    return locked_until > _now()


def record_failed_login(user: User) -> None:
    """Increment counter; lock the account when the threshold is hit."""
    threshold = current_app.config.get("ACCOUNT_LOCKOUT_THRESHOLD", 5)
    minutes = current_app.config.get("ACCOUNT_LOCKOUT_MINUTES", 15)

    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= threshold:
        user.locked_until = _now() + datetime.timedelta(minutes=minutes)
    user.upsert()


def record_successful_login(user: User) -> None:
    """Reset the lockout state on a clean login."""
    if user.failed_login_count or user.locked_until:
        user.failed_login_count = 0
        user.locked_until = None
        user.upsert()
