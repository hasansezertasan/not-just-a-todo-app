# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Slow-query event listener.

Hooks SQLAlchemy's `before/after_cursor_execute` to time every statement;
warns on outliers. Catches N+1 patterns, missing indexes, accidental
table scans. Pairs with the JSON formatter — `duration_ms` and
`statement` land as queryable structured fields.
"""

import logging
import time
from typing import TYPE_CHECKING

from sqlalchemy import event

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def register_slow_query_logger(engine: Engine, threshold_ms: int = 100) -> None:
    """Warn-log every SQL statement that exceeds `threshold_ms`."""

    @event.listens_for(engine, "before_cursor_execute")
    def _start_timer(_conn, _cursor, _statement, _parameters, context, _executemany):
        context._query_start_ts = time.perf_counter()  # noqa: SLF001

    @event.listens_for(engine, "after_cursor_execute")
    def _check_threshold(
        _conn, _cursor, statement, parameters, context, executemany
    ):
        elapsed_ms = (time.perf_counter() - context._query_start_ts) * 1000  # noqa: SLF001
        if elapsed_ms < threshold_ms:
            return
        logger.warning(
            "slow query: %.1fms",
            elapsed_ms,
            extra={
                "duration_ms": round(elapsed_ms, 2),
                "statement": statement[:500],
                "param_count": len(parameters) if parameters else 0,
                "executemany": executemany,
            },
        )
