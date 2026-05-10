# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Factory invariants — verify create_app() honors Settings across env profiles."""

from datetime import timedelta

import pytest
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Settings
from app.factory import create_app


def _settings(**overrides) -> Settings:
    base = {
        "app_env": "testing",
        "sqlalchemy_database_url": "sqlite:///:memory:",
        "session_secret_key": "test-secret",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_create_app_returns_independent_instances() -> None:
    """Factory must build fresh apps — no shared global state."""
    a = create_app(_settings())
    b = create_app(_settings())
    assert a is not b


def test_proxy_fix_is_attached() -> None:
    app = create_app(_settings())
    assert isinstance(app.wsgi_app, ProxyFix)


def test_healthz_route_registered() -> None:
    app = create_app(_settings())
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/healthz" in rules


def test_login_view_endpoint_wired() -> None:
    """Flask-Login must redirect anonymous users to the admin login view."""
    app = create_app(_settings())
    with app.app_context():
        from app.extensions import login_manager

        assert login_manager.login_view is not None
        assert "login_view" in login_manager.login_view


def test_session_protection_strong() -> None:
    from app.extensions import login_manager

    assert login_manager.session_protection == "strong"


def test_cli_commands_registered() -> None:
    app = create_app(_settings())
    # Expect the `seed` AppGroup with `users` + `sequences` subcommands.
    assert "seed" in app.cli.commands
    seed_group = app.cli.commands["seed"]
    assert {"users", "sequences"} <= set(seed_group.commands.keys())


def test_session_lifetime_is_timedelta() -> None:
    app = create_app(_settings(permanent_session_lifetime_days=14))
    assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(days=14)


def test_production_requires_explicit_secret() -> None:
    """Production must reject the default placeholder secret."""
    with pytest.raises(ValueError, match="SESSION_SECRET_KEY"):
        Settings(app_env="production")  # type: ignore[arg-type]


def test_production_secure_cookies() -> None:
    settings = Settings(
        app_env="production",
        session_secret_key="real-prod-secret",  # type: ignore[arg-type]
    )
    flask_config = settings.to_flask()
    assert flask_config["SESSION_COOKIE_SECURE"] is True
    assert flask_config["SESSION_COOKIE_HTTPONLY"] is True
    assert flask_config["PREFERRED_URL_SCHEME"] == "https"


def test_development_loose_cookies() -> None:
    settings = Settings(app_env="development")
    flask_config = settings.to_flask()
    assert flask_config["SESSION_COOKIE_SECURE"] is False
    assert flask_config["PREFERRED_URL_SCHEME"] == "http"


def test_sqlalchemy_echo_off_by_default() -> None:
    settings = _settings()
    assert settings.to_flask()["SQLALCHEMY_ECHO"] is False


def test_static_max_age_long_in_production() -> None:
    """flask-static-digest fingerprints filenames → safe to cache 1 year."""
    settings = Settings(
        app_env="production",
        session_secret_key="real",  # type: ignore[arg-type]
    )
    assert settings.to_flask()["SEND_FILE_MAX_AGE_DEFAULT"] == 31536000


def test_static_max_age_zero_in_dev() -> None:
    """Dev gets 0 so CSS/JS edits surface without hard refresh."""
    settings = Settings(app_env="development")
    assert settings.to_flask()["SEND_FILE_MAX_AGE_DEFAULT"] == 0


def test_sqlalchemy_echo_propagates_when_enabled() -> None:
    """`SQLALCHEMY_ECHO=true` flows through Settings to app.config."""
    settings = _settings(sqlalchemy_echo=True)
    app = create_app(settings)
    assert app.config["SQLALCHEMY_ECHO"] is True


def test_extensions_init_app_called() -> None:
    """Bootstrap, db, migrate, admin, login_manager must all be bound to the app."""
    app = create_app(_settings())
    with app.app_context():
        assert "sqlalchemy" in app.extensions
        assert "migrate" in app.extensions
        assert "bootstrap" in app.extensions
        assert "admin" in app.extensions
        # Flask-Login attaches itself directly to the app object.
        assert getattr(app, "login_manager", None) is not None
