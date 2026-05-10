# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""HaveIBeenPwned password-breach lookup.

Uses k-Anonymity: only the first 5 chars of the SHA-1 hash leave the
host; the API returns all suffixes that share that prefix and we match
locally. The plaintext password never crosses the wire.

Gated by `PASSWORD_BREACH_CHECK_ENABLED`. Defaults off so existing
users + tests aren't surprised by network calls during registration.

Fail-open on API/network errors — registration shouldn't break because
the external service is degraded. The cost of a missed breach check
is lower than the cost of denying signup during an HIBP outage.
"""

import hashlib
import logging
from urllib.error import URLError
from urllib.request import (  # noqa: S310 — fixed https URL  # nosec B310
    Request,
    urlopen,
)

from flask import current_app

logger = logging.getLogger(__name__)

_HIBP_URL = "https://api.pwnedpasswords.com/range/{prefix}"  # noqa: S105


def breach_count(password: str, *, timeout: float | None = None) -> int | None:
    """Return how many times `password` appears in known breaches.

    Returns:
        - non-negative int: count (0 means clean).
        - None: API unreachable; caller decides policy.
    """
    if timeout is None:
        timeout = current_app.config.get("PASSWORD_BREACH_API_TIMEOUT_SECONDS", 2.0)
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()  # noqa: S324  # nosec B324
    prefix, suffix = sha1[:5], sha1[5:]

    req = Request(  # noqa: S310 — URL is a fixed-scheme constant  # nosec B310
        _HIBP_URL.format(prefix=prefix),
        headers={"User-Agent": "not-just-a-todo-app", "Add-Padding": "true"},
    )
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310  # nosec B310
            body = resp.read().decode("utf-8")
    except (URLError, TimeoutError) as exc:
        logger.warning("HIBP unavailable: %s", exc)
        return None

    for line in body.splitlines():
        line_suffix, _, count = line.partition(":")
        if line_suffix == suffix:
            return int(count)
    return 0


def is_breached(password: str) -> bool:
    """Wrapper honoring the feature flag and fail-open policy.

    Returns True only when the API confirmed the password is breached.
    Returns False when the flag is off OR the API was unreachable —
    callers don't need to distinguish the two cases.
    """
    if not current_app.config.get("PASSWORD_BREACH_CHECK_ENABLED", False):
        return False
    count = breach_count(password)
    return count is not None and count > 0
