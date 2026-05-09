# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Account-lockout service tests."""

import datetime
from typing import TYPE_CHECKING

from app.services import auth as auth_service

if TYPE_CHECKING:
    from app.db.models.users import User


def test_fresh_user_is_not_locked(user: User) -> None:
    assert auth_service.is_locked(user) is False


def test_record_failed_login_increments_counter(user: User) -> None:
    auth_service.record_failed_login(user)
    assert user.failed_login_count == 1
    assert user.locked_until is None


def test_threshold_triggers_lockout(user: User) -> None:
    """Hit the configured threshold (default 5) and expect a lock window."""
    for _ in range(5):
        auth_service.record_failed_login(user)
    assert auth_service.is_locked(user) is True
    assert user.locked_until is not None


def test_successful_login_clears_state(user: User) -> None:
    for _ in range(3):
        auth_service.record_failed_login(user)
    auth_service.record_successful_login(user)
    assert user.failed_login_count == 0
    assert user.locked_until is None
    assert auth_service.is_locked(user) is False


def test_expired_lock_no_longer_locks(user: User) -> None:
    """A lock from the past should not register as currently locked."""
    user.failed_login_count = 5
    # Naive UTC to match what SQLite returns from `locked_until`.
    user.locked_until = datetime.datetime.now(datetime.UTC).replace(
        tzinfo=None
    ) - datetime.timedelta(minutes=1)
    user.upsert()
    assert auth_service.is_locked(user) is False
