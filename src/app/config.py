# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>

from datetime import timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

basedir = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = Path(__file__).parent / "db" / "fixtures"
DEFAULT_DEV_SECRET = "super-secret"  # noqa: S105  # nosec B105 — placeholder; production rejects via model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "testing", "production"] = "development"
    session_secret_key: SecretStr = SecretStr(DEFAULT_DEV_SECRET)
    permanent_session_lifetime_days: int = Field(default=7, ge=1)
    sqlalchemy_database_url: str = f"sqlite:///{basedir / 'instance' / 'db.sqlite3'}"
    session_cookie_samesite: Literal["Lax", "Strict", "None"] = "Lax"
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    db_pool_pre_ping: bool = True
    db_pool_size: int = Field(default=5, ge=1)
    db_pool_max_overflow: int = Field(default=10, ge=0)
    db_pool_timeout_seconds: int = Field(default=30, ge=1)
    db_pool_recycle_seconds: int = Field(default=3600, ge=0)
    db_statement_timeout_ms: int = Field(default=0, ge=0)  # 0 = disabled; Postgres only
    sqlalchemy_echo: bool = False
    metrics_enabled: bool = True
    otel_endpoint: str | None = None
    otel_service_name: str = "not-just-a-todo-app"
    rate_limit_storage_uri: str = "memory://"
    rate_limit_login: str = "10 per minute"
    rate_limit_register: str = "5 per hour"
    account_lockout_threshold: int = Field(default=5, ge=1)
    account_lockout_minutes: int = Field(default=15, ge=1)
    debug_toolbar_enabled: bool = False

    @model_validator(mode="after")
    def _require_secret_in_production(self) -> Settings:
        if (
            self.app_env == "production"
            and self.session_secret_key.get_secret_value() == DEFAULT_DEV_SECRET
        ):
            msg = "SESSION_SECRET_KEY must be set explicitly when APP_ENV=production"
            raise ValueError(msg)
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def to_flask(self) -> dict[str, Any]:
        engine_options: dict[str, Any] = {
            "pool_pre_ping": self.db_pool_pre_ping,
            "pool_recycle": self.db_pool_recycle_seconds,
        }
        # SQLite uses a static pool by default; pool_size + overflow only
        # apply to connection-pool-based dialects (Postgres, MySQL).
        if not self.sqlalchemy_database_url.startswith("sqlite"):
            engine_options["pool_size"] = self.db_pool_size
            engine_options["max_overflow"] = self.db_pool_max_overflow
            engine_options["pool_timeout"] = self.db_pool_timeout_seconds

        # Postgres: bound runaway query duration server-side. See
        # docs/operations.md for the coordinated-timeout discipline. SQLite
        # has no equivalent — flag is a no-op there.
        if (
            "postgresql" in self.sqlalchemy_database_url
            and self.db_statement_timeout_ms > 0
        ):
            engine_options["connect_args"] = {
                "options": f"-c statement_timeout={self.db_statement_timeout_ms}",
            }

        return {
            "APP_ENV": self.app_env,
            "SECRET_KEY": self.session_secret_key.get_secret_value(),
            "PERMANENT_SESSION_LIFETIME": timedelta(
                days=self.permanent_session_lifetime_days
            ),
            "SQLALCHEMY_DATABASE_URI": self.sqlalchemy_database_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SQLALCHEMY_ECHO": self.sqlalchemy_echo,
            "SQLALCHEMY_ENGINE_OPTIONS": engine_options,
            # Pairs with flask-static-digest: hashed filenames change on deploy,
            # so the file at any given URL is immutable → safe to cache for a
            # year. Dev gets 0 so CSS/JS edits surface without hard refresh.
            "SEND_FILE_MAX_AGE_DEFAULT": 31536000 if self.is_production else 0,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SECURE": self.is_production,
            "SESSION_COOKIE_SAMESITE": self.session_cookie_samesite,
            "PREFERRED_URL_SCHEME": "https" if self.is_production else "http",
            "ACCOUNT_LOCKOUT_THRESHOLD": self.account_lockout_threshold,
            "ACCOUNT_LOCKOUT_MINUTES": self.account_lockout_minutes,
        }
