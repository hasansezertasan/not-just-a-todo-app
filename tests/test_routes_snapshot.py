# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Snapshot of the registered URL map.

Catches:
- routes added without test coverage
- routes removed during refactors
- changed HTTP methods on existing routes
- endpoint renames

When the registered surface intentionally changes, refresh the snapshot:

    uv run pytest tests/test_routes_snapshot.py --snapshot-update

The diff in `tests/__snapshots__/test_routes_snapshot.ambr` is what
reviewers should sanity-check on every PR.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def test_url_map_snapshot(app: Flask, snapshot) -> None:
    rules = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
        if rule.endpoint == "static":
            continue  # auto-registered, not interesting
        # Drop HEAD/OPTIONS — Werkzeug auto-derives them from GET.
        methods = sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})
        rules.append(f"{rule.rule:60s} {','.join(methods):20s} {rule.endpoint}")

    rendered = "\n".join(rules)
    assert rendered == snapshot
