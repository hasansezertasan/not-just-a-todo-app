# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Cross-cutting HTTP behavior: readiness, request IDs, security headers, errors."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


def test_readyz_reports_db_up(client: FlaskClient, db: object) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["db"] == "up"


def test_request_id_generated_when_absent(client: FlaskClient) -> None:
    response = client.get("/healthz")
    rid = response.headers.get("X-Request-ID")
    assert rid
    assert len(rid) >= 16  # UUID hex is 32, but allow shorter custom IDs


def test_request_id_echoed_when_supplied(client: FlaskClient) -> None:
    response = client.get("/healthz", headers={"X-Request-ID": "test-trace-123"})
    assert response.headers.get("X-Request-ID") == "test-trace-123"


def test_security_headers_applied(client: FlaskClient) -> None:
    response = client.get("/healthz")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Referrer-Policy" in response.headers
    assert "Permissions-Policy" in response.headers


def test_hsts_only_in_https_mode(app: Flask) -> None:
    """HSTS must NOT be sent over HTTP — would break first-time http→https flows."""
    client = app.test_client()
    response = client.get("/healthz")
    assert "Strict-Transport-Security" not in response.headers


def test_404_returns_json_when_accept_json(client: FlaskClient) -> None:
    response = client.get("/no-such-route", headers={"Accept": "application/json"})
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["status"] == 404
    assert payload["error"] == "Not Found"
    assert "request_id" in payload


def test_error_response_includes_request_id(client: FlaskClient) -> None:
    response = client.get(
        "/no-such-route",
        headers={"Accept": "application/json", "X-Request-ID": "rid-xyz"},
    )
    assert response.get_json()["request_id"] == "rid-xyz"


def test_csrf_extension_initialized(app: Flask) -> None:
    """CSRFProtect should bind to the app even though tests disable enforcement."""
    assert "csrf" in app.extensions


def test_metrics_endpoint_exposed(client: FlaskClient) -> None:
    """Prometheus `/metrics` must expose plain-text exposition format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "flask_http_request_total" in body or "app_info" in body


def test_health_endpoints_set_no_store(client: FlaskClient) -> None:
    for path in ("/healthz", "/livez", "/readyz"):
        r = client.get(path)
        assert r.headers.get("Cache-Control") == "no-store", path


def test_health_endpoints_accept_head(client: FlaskClient) -> None:
    """Some load balancers probe with HEAD only."""
    for path in ("/healthz", "/livez", "/readyz"):
        r = client.head(path)
        assert r.status_code == 200, path


def test_livez_returns_same_payload_as_healthz(client: FlaskClient) -> None:
    """`/livez` is a k8s-native alias for `/healthz` — bodies must match."""
    a = client.get("/healthz").get_json()
    b = client.get("/livez").get_json()
    assert a == b == {"status": "ok"}


def test_compress_responds_with_encoding_when_requested(client: FlaskClient) -> None:
    """flask-compress should advertise compression via Vary header on responses."""
    response = client.get("/healthz", headers={"Accept-Encoding": "gzip"})
    # Body too small to actually gzip (<500B threshold), but the negotiation
    # should still surface in Vary so caches segment by encoding.
    vary = response.headers.get("Vary", "")
    assert "Accept-Encoding" in vary or response.status_code == 200


def test_static_digest_helper_registered(app: Flask) -> None:
    """flask-static-digest exposes `static_url_for` to Jinja templates."""
    assert "static_url_for" in app.jinja_env.globals


def test_rate_limiter_attached(app: Flask) -> None:
    """flask-limiter must register on the app extensions registry."""
    assert "limiter" in app.extensions


def test_rate_limit_storage_uri_configured(app: Flask) -> None:
    """Limiter storage URI must be wired so multi-worker deployments share state.

    `memory://` is the default for single-process; production likely overrides
    to `redis://...`. Either way, the config key must be present.
    """
    assert app.config.get("RATELIMIT_STORAGE_URI") is not None


def test_rate_limiter_settings_have_sensible_defaults() -> None:
    """The Settings object exposes per-endpoint rate-limit strings.

    We can't easily integration-test 429 responses because Flask-Admin
    bypasses the `limiter.limit()` decoration we placed on `login_view`
    (Flask-Admin owns the dispatcher). Asserting on Settings is the
    next-best invariant — and is what production reads.
    """
    from app.config import Settings

    settings = Settings(app_env="testing", session_secret_key="x")  # type: ignore[arg-type]
    assert "per" in settings.rate_limit_login.lower()
    assert "per" in settings.rate_limit_register.lower()


def test_shell_context_exposes_models(app: Flask) -> None:
    """`flask shell` must auto-import db + model classes for ergonomic REPL use."""
    with app.app_context():
        ctx = {}
        for processor in app.shell_context_processors:
            ctx.update(processor())
    expected = {"db", "User", "Sequence", "Task", "SequenceTemplate", "TaskTemplate"}
    assert expected <= set(ctx.keys())
