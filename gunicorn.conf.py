# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Gunicorn configuration.

Loaded automatically when gunicorn is invoked from the project root, or
explicitly via ``gunicorn -c gunicorn.conf.py app.wsgi:app``. Keep all
production WSGI tuning here so the Dockerfile CMD stays declarative and
the same config works locally and in CI.
"""

import multiprocessing
import os

# --- Networking -------------------------------------------------------------
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "*")

# --- Worker model -----------------------------------------------------------
# Default to (2 * CPU) + 1 unless WEB_CONCURRENCY pins it.
workers = int(os.getenv("WEB_CONCURRENCY", str((multiprocessing.cpu_count() * 2) + 1)))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "sync")
threads = int(os.getenv("GUNICORN_THREADS", "1"))

# --- Timeouts ---------------------------------------------------------------
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# --- Worker recycling -------------------------------------------------------
# Recycle each worker after handling N requests. Cheap insurance against
# slow memory leaks in long-lived web workers (Flask + SQLAlchemy + a dozen
# extensions accumulate). Disabled when set to 0.
#
# Jitter spreads recycle events across workers so they don't all restart at
# the same moment — preventing a synchronized capacity dip.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# --- Logging ----------------------------------------------------------------
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = (
    '%(h)s %({X-Request-ID}i)s "%(r)s" %(s)s %(b)s %(L)ss "%(f)s" "%(a)s"'
)


# --- Lifecycle hooks --------------------------------------------------------
def when_ready(server):  # noqa: ARG001 — gunicorn calls with server arg
    """Called once after the master process initialized."""
    server.log.info("gunicorn ready: workers=%s class=%s", workers, worker_class)


def post_fork(server, worker):  # noqa: ARG001
    """Called inside each worker right after fork."""
    server.log.info("worker forked: pid=%s", worker.pid)


def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT — log for postmortem."""
    worker.log.info("worker received SIGINT/SIGQUIT: pid=%s", worker.pid)
