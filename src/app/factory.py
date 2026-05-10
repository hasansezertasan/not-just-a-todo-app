# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Application factory.

Builds Flask app instances. Keep this module side-effect free: ``create_app``
is the only thing the WSGI entrypoint and tests should call.
"""

import logging
from logging.config import dictConfig
from pathlib import Path

from flask import Flask, jsonify
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from app import commands
from app.admin import admin
from app.config import Settings, basedir
from app.db.models.base import Base, db
from app.extensions import (
    bootstrap,
    compress,
    csrf,
    limiter,
    login_manager,
    migrate,
    static_digest,
)
from app.middleware import (
    register_canonical_log_line,
    register_error_handlers,
    register_request_id,
    register_security_headers,
    register_sentry_user_context,
)

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings()

    _configure_logging(settings.log_level, settings.log_format)
    _init_sentry(settings)

    app = Flask(
        __name__,
        instance_relative_config=True,
        instance_path=str(basedir / "instance"),
    )
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(settings.to_flask())

    app.config["RATELIMIT_STORAGE_URI"] = settings.rate_limit_storage_uri

    _init_extensions(app)
    _register_cli(app)
    _register_health(app)
    _register_shell_context(app)
    _register_teardown(app)
    _apply_rate_limits(settings)
    _init_debug_toolbar(app, settings)
    register_request_id(app)
    register_security_headers(app)
    register_error_handlers(app)
    register_sentry_user_context(app)
    register_canonical_log_line(app)
    _init_metrics(app, settings)
    _init_otel(app, settings)
    _apply_proxy_fix(app)

    app.logger.info("app booted env=%s", settings.app_env)
    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    # sqlalchemy-mixins' AllFeaturesMixin needs a session bound on the Base
    # class so `Model.query` / `Model.find_by_id` work without an explicit
    # `db.session.query(Model)` call.
    Base.set_session(db.session)
    migrate.init_app(
        app=app,
        db=db,
        directory=str(Path(__file__).parent / "db" / "migrations"),
        # Forwarded into alembic context so `flask db migrate` autogeneration
        # detects column type and server_default changes (skipped by default).
        compare_type=True,
        compare_server_default=True,
    )
    bootstrap.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = admin.index_view.endpoint + ".login_view"
    csrf.init_app(app)
    compress.init_app(app)
    static_digest.init_app(app)
    limiter.init_app(app)


def _register_cli(app: Flask) -> None:
    app.cli.add_command(commands.seed)


def _register_health(app: Flask) -> None:
    """Liveness vs readiness split.

    `/healthz` answers "is the process alive" — no external dependencies.
    `/readyz` answers "can the process serve traffic" — verifies the DB.
    Orchestrators that distinguish the two (k8s) get accurate signals.

    Both routes accept HEAD (some load balancers probe HEAD-only) and set
    `Cache-Control: no-store` so intermediaries / CDNs don't serve stale
    health data.
    """
    no_cache = {"Cache-Control": "no-store"}

    # `/livez` is the modern k8s-native liveness path (≥1.16); `/healthz`
    # remains as a legacy alias so older probes still resolve.
    @app.route("/healthz", methods=["GET", "HEAD"])
    @app.route("/livez", methods=["GET", "HEAD"])
    def healthz():
        response = jsonify(status="ok")
        response.headers.update(no_cache)
        return response, 200

    @app.route("/readyz", methods=["GET", "HEAD"])
    def readyz():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 — readiness must not raise
            # Full detail goes to logs only — `/readyz` is unauthenticated
            # and often public via load balancers; raw driver errors can
            # leak DB topology / driver versions to attackers.
            logger.warning("readiness check failed: %s", exc, exc_info=True)
            response = jsonify(status="error", db="down")
            response.headers.update(no_cache)
            return response, 503
        response = jsonify(status="ok", db="up")
        response.headers.update(no_cache)
        return response, 200


def _register_shell_context(app: Flask) -> None:
    """Auto-import models into `flask shell`."""

    @app.shell_context_processor
    def _shell_ctx():
        from app.db.models.sequences import Sequence, Task
        from app.db.models.templates import SequenceTemplate, TaskTemplate
        from app.db.models.users import User

        return {
            "db": db,
            "User": User,
            "Sequence": Sequence,
            "Task": Task,
            "SequenceTemplate": SequenceTemplate,
            "TaskTemplate": TaskTemplate,
        }


def _register_teardown(app: Flask) -> None:
    """Guarantee session.remove() even when a request raises mid-handler."""

    @app.teardown_appcontext
    def _shutdown_session(exception=None) -> None:
        if exception is not None:
            db.session.rollback()
        db.session.remove()


def _apply_rate_limits(settings: Settings) -> None:
    """Throttle high-risk auth endpoints.

    The IndexView from `app.admin` exposes `login_view` and `register_view`
    bound methods; flask-limiter accepts callables for `.limit(...)`.
    """
    from app.admin import admin

    index_view = admin.index_view
    limiter.limit(settings.rate_limit_login)(index_view.login_view)
    limiter.limit(settings.rate_limit_register)(index_view.register_view)


def _init_debug_toolbar(app: Flask, settings: Settings) -> None:
    """Mount Flask-DebugToolbar in development only.

    Soft-import: it's a dev-group dependency, not in production wheels.
    """
    if not settings.debug_toolbar_enabled or settings.is_production:
        return
    try:
        from flask_debugtoolbar import DebugToolbarExtension
    except ImportError:
        logger.warning("DEBUG_TOOLBAR_ENABLED but flask-debugtoolbar not installed")
        return
    app.config.setdefault("DEBUG_TB_INTERCEPT_REDIRECTS", False)
    DebugToolbarExtension(app)


def _apply_proxy_fix(app: Flask) -> None:
    app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )


def _init_metrics(app: Flask, settings: Settings) -> None:
    """Expose `/metrics` (Prometheus) — request count, latency histograms, etc.

    `prometheus-flask-exporter` auto-tracks every Flask route. Disable via
    `METRICS_ENABLED=false` if a sidecar handles scraping differently.

    A per-app `CollectorRegistry` keeps tests (which build many apps) from
    colliding on the global default registry.
    """
    if not settings.metrics_enabled:
        return
    from prometheus_client import CollectorRegistry
    from prometheus_flask_exporter import PrometheusMetrics

    from app.observability import metrics as domain_metrics

    registry = CollectorRegistry()
    metrics = PrometheusMetrics(app, group_by="endpoint", registry=registry)
    metrics.info("app_info", "Application info", version="0.1.0", env=settings.app_env)
    # Domain counters share the per-app registry — same /metrics endpoint
    # serves both flask_* HTTP metrics and app_* business metrics.
    app.extensions["app_metrics"] = domain_metrics.build(registry)


def _init_otel(app: Flask, settings: Settings) -> None:
    """Wire OpenTelemetry only when an OTLP endpoint is configured.

    Soft-import: the `otel` extras may not be installed in slim builds.
    Auto-instruments Flask requests + SQLAlchemy queries; spans flow to the
    configured OTLP collector.
    """
    if not settings.otel_endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OTEL_ENDPOINT set but opentelemetry extras not installed; "
            "install with `pip install .[otel]`",
        )
        return

    import os
    import socket

    # Standard OTel semantic-convention resource attributes:
    # - service.version groups spans by deploy (same GIT_SHA used by Sentry).
    # - service.instance.id distinguishes replicas / gunicorn workers so a
    #   misbehaving pod is identifiable in collector queries.
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": os.getenv("GIT_SHA") or "0.0.0",
        "service.instance.id": f"{socket.gethostname()}-{os.getpid()}",
        "deployment.environment": settings.app_env,
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_endpoint))
    )
    trace.set_tracer_provider(provider)

    FlaskInstrumentor().instrument_app(app)
    with app.app_context():
        SQLAlchemyInstrumentor().instrument(engine=db.engine)


def _init_sentry(settings: Settings) -> None:
    """Wire Sentry only when a DSN is provided. Optional dep — soft import.

    `release` is sourced from `GIT_SHA` (CI build-arg) so Sentry can group
    errors by deploy, surface regressions, and run release-health metrics.
    """
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
    except ImportError:
        logger.warning("SENTRY_DSN set but sentry-sdk not installed; skipping")
        return

    import os

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment=settings.app_env,
        release=os.getenv("GIT_SHA") or None,
        send_default_pii=False,
    )


class _RequestIdFilter(logging.Filter):
    """Inject the current request's ID onto every log record.

    Reads from `flask.g.request_id` if a request context is active. Outside
    a request (CLI, gunicorn boot, background workers) the field is `-`.
    Allows aggregators to correlate logs across the request lifecycle.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from flask import g, has_request_context

            record.request_id = (
                g.get("request_id", "-") if has_request_context() else "-"
            )
        except Exception:  # noqa: BLE001 — never let logging break the app
            record.request_id = "-"
        return True


def _configure_logging(level: str, fmt: str = "json") -> None:
    """Configure stdout logging.

    `fmt="json"` emits one JSON object per line — log aggregators (Loki,
    Datadog, ELK) parse natively. `fmt="text"` keeps human-friendly output
    for local dev.
    """
    if fmt == "json":
        formatter = {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
            "rename_fields": {
                "asctime": "ts",
                "levelname": "level",
                "name": "logger",
            },
        }
    else:
        formatter = {
            "format": (
                "[%(asctime)s] %(levelname)s %(name)s [rid=%(request_id)s]: %(message)s"
            ),
        }

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": _RequestIdFilter}},
        "formatters": {"default": formatter},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
                "filters": ["request_id"],
            },
        },
        "root": {"level": level, "handlers": ["stdout"]},
    })
