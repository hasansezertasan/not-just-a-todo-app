# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Domain-specific Prometheus counters.

The auto-tracked Flask metrics (`flask_http_request_total`, latency
histograms) measure *endpoint hit rate*. These counters measure
*outcomes* — what mattered semantically. Login failure rate, lockout
rate, registration funnel.

Counters are bound to the per-app `CollectorRegistry` (not the global
default) so multi-app test suites don't collide. Look them up at hook
sites via `current_app.extensions["app_metrics"]`.
"""

from typing import TYPE_CHECKING

from flask import current_app

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry, Counter


def build(registry: CollectorRegistry) -> dict[str, Counter]:
    """Construct the domain counters bound to the given registry.

    Called once per app from the factory's `_init_metrics`.
    """
    from prometheus_client import Counter

    return {
        "login_attempts": Counter(
            "app_login_attempts_total",
            "Login attempts by outcome.",
            ["result"],  # success | invalid | locked
            registry=registry,
        ),
        "account_lockouts": Counter(
            "app_account_lockouts_total",
            "Times an account was locked due to threshold breach.",
            registry=registry,
        ),
        "registrations": Counter(
            "app_registrations_total",
            "Registration attempts by outcome.",
            ["result"],  # success | duplicate_username
            registry=registry,
        ),
    }


def get(name: str) -> Counter | None:
    """Fetch a named counter from the active app, returning None if metrics
    are disabled (so hooks can be wired unconditionally).
    """
    return current_app.extensions.get("app_metrics", {}).get(name)
