# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""HTTP middleware: request IDs, security headers, error handlers.

Each function takes a ``Flask`` app and registers its hook(s); the factory
calls them in order. Keeping middleware out of the factory body lets us
unit-test each concern in isolation.
"""

import logging
import uuid

from flask import Flask, Response, current_app, g, jsonify, render_template, request

logger = logging.getLogger(__name__)


def register_sentry_user_context(app: Flask) -> None:
    """Bind the authenticated user to every Sentry event.

    Sentry's UI then shows "this error affects N users" instead of just
    occurrence counts — distinguishes single-user weird-state bugs from
    broad outages. Sends `id` + `username` only; no email/PII.
    """

    @app.before_request
    def _bind_user_to_sentry() -> None:
        try:
            import sentry_sdk
        except ImportError:
            return
        try:
            from flask_login import current_user
        except ImportError:
            return
        if getattr(current_user, "is_authenticated", False):
            sentry_sdk.set_user({
                "id": current_user.id,
                "username": current_user.username,
            })


_OBS_PATHS_SKIP_CANONICAL_LOG = ("/healthz", "/livez", "/readyz", "/metrics")


def register_canonical_log_line(app: Flask) -> None:
    """Emit one structured log record per request — wide-event pattern.

    A single record per request is the densest unit of observability:
    paired with the JSON formatter, every `extra={}` key becomes a
    queryable field in Loki/Datadog/ELK. Replaces ~10 ad-hoc log calls
    with one canonical line whose schema is grep-friendly.

    Skipped on probe / metrics paths to keep the access log focused on
    user-facing traffic.
    """
    import time

    from flask import request
    from flask_login import current_user

    @app.before_request
    def _start_canonical_timer() -> None:
        g.canonical_start = time.perf_counter()

    @app.after_request
    def _emit_canonical(response: Response) -> Response:
        if request.path.startswith(_OBS_PATHS_SKIP_CANONICAL_LOG):
            return response

        start = g.get("canonical_start")
        duration_ms = round((time.perf_counter() - start) * 1000, 2) if start else None

        user_id = (
            getattr(current_user, "id", None)
            if getattr(current_user, "is_authenticated", False)
            else None
        )

        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "remote_addr": request.remote_addr,
                "endpoint": request.endpoint,
                "content_length": response.calculate_content_length(),
            },
        )
        return response


def register_request_id(app: Flask) -> None:
    """Assign a UUID per request, log it, and echo it back in `X-Request-ID`.

    Callers can supply their own ID via the inbound header (useful for
    cross-service tracing); otherwise we generate one. The ID is bound to
    `flask.g` so views and templates can read it.
    """

    @app.before_request
    def _attach_request_id() -> None:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.request_id = rid

    @app.after_request
    def _emit_request_id(response: Response) -> Response:
        response.headers["X-Request-ID"] = g.get("request_id", "")
        return response


def register_security_headers(app: Flask) -> None:
    """Apply a baseline set of security response headers.

    Conservative defaults: deny iframes, lock down referrer, force MIME
    sniffing off, and (in production) set HSTS. CSP is intentionally
    permissive here because Flask-Admin loads inline scripts/styles from
    its own templates; tighten per-route if the app evolves.
    """

    @app.after_request
    def _apply_headers(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        if current_app.config.get("PREFERRED_URL_SCHEME") == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


def register_error_handlers(app: Flask) -> None:
    """Render consistent error responses; respect Accept header for JSON."""

    def _wants_json() -> bool:
        if request.accept_mimetypes.best == "application/json":
            return True
        return request.path.startswith(("/healthz", "/livez", "/readyz"))

    def _render(code: int, message: str):
        rid = g.get("request_id", "")
        if _wants_json():
            return jsonify(error=message, status=code, request_id=rid), code
        try:
            return (
                render_template(f"errors/{code}.html", message=message, request_id=rid),
                code,
            )
        except Exception:  # noqa: BLE001 — fallback when template missing
            return jsonify(error=message, status=code, request_id=rid), code

    @app.errorhandler(401)
    def _unauthorized(_e):
        return _render(401, "Unauthorized")

    @app.errorhandler(403)
    def _forbidden(_e):
        return _render(403, "Forbidden")

    @app.errorhandler(404)
    def _not_found(_e):
        return _render(404, "Not Found")

    @app.errorhandler(500)
    def _server_error(e):
        # Full detail (with traceback) goes to logs — request_id correlates
        # the user-facing 500 with the structured log entry.
        logger.error(
            "unhandled exception",
            extra={"request_id": g.get("request_id")},
        )
        # Outside dev, don't leak exception type/message — debuggers should
        # use the request_id to look up the full record in logs.
        is_dev = current_app.config.get("APP_ENV") == "development"
        message = f"{type(e).__name__}: {e}" if is_dev else "Internal Server Error"
        return _render(500, message)
