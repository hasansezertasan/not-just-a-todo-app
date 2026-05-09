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
        logger.error("unhandled exception", extra={"request_id": g.get("request_id")})
        # Don't leak internal details in production.
        message = (
            "Internal Server Error"
            if current_app.config.get("ENV") == "production"
            else f"{type(e).__name__}: {e}"
        )
        return _render(500, message)
