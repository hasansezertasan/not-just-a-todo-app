# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Factory invariants — verify create_app() honors Settings across env profiles."""

from datetime import timedelta

import pytest
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import DEFAULT_DEV_SECRET, Settings
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


def test_production_requires_explicit_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production must reject the default placeholder secret."""
    monkeypatch.delenv("SESSION_SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="SESSION_SECRET_KEY"):
        Settings(
            app_env="production",
            session_secret_key=DEFAULT_DEV_SECRET,  # type: ignore[arg-type]
        )


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


def test_statement_timeout_no_op_for_sqlite() -> None:
    """SQLite has no statement_timeout — connect_args must NOT be set."""
    settings = _settings(db_statement_timeout_ms=25000)
    engine_opts = settings.to_flask()["SQLALCHEMY_ENGINE_OPTIONS"]
    assert "connect_args" not in engine_opts


def test_statement_timeout_applied_for_postgres() -> None:
    """Postgres URLs must surface the timeout via connect_args.options."""
    settings = _settings(
        sqlalchemy_database_url="postgresql://localhost/test",
        db_statement_timeout_ms=25000,
    )
    engine_opts = settings.to_flask()["SQLALCHEMY_ENGINE_OPTIONS"]
    assert engine_opts["connect_args"] == {"options": "-c statement_timeout=25000"}


def test_statement_timeout_disabled_when_zero() -> None:
    """0 means disabled even for Postgres — no connect_args set."""
    settings = _settings(
        sqlalchemy_database_url="postgresql://localhost/test",
        db_statement_timeout_ms=0,
    )
    engine_opts = settings.to_flask()["SQLALCHEMY_ENGINE_OPTIONS"]
    assert "connect_args" not in engine_opts


def test_pool_overflow_and_timeout_applied_for_postgres() -> None:
    """pool_size, max_overflow, pool_timeout must surface for non-SQLite URLs."""
    settings = _settings(
        sqlalchemy_database_url="postgresql://localhost/test",
        db_pool_size=8,
        db_pool_max_overflow=20,
        db_pool_timeout_seconds=15,
    )
    opts = settings.to_flask()["SQLALCHEMY_ENGINE_OPTIONS"]
    assert opts["pool_size"] == 8
    assert opts["max_overflow"] == 20
    assert opts["pool_timeout"] == 15


def test_pool_options_omitted_for_sqlite() -> None:
    """SQLite uses StaticPool — pool_size/max_overflow/pool_timeout are no-ops."""
    settings = _settings(db_pool_size=8, db_pool_max_overflow=20)
    opts = settings.to_flask()["SQLALCHEMY_ENGINE_OPTIONS"]
    assert "pool_size" not in opts
    assert "max_overflow" not in opts
    assert "pool_timeout" not in opts


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
