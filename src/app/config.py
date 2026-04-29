# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
import os
from pathlib import Path

basedir = Path(__name__).resolve().parent


class FlaskConfig:
    # [Configuration Handling — Flask Documentation (2.3.x)](https://flask.palletsprojects.com/en/2.3.x/config/)
    SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "super-secret")
    """SECRET_KEY will be used for securely signing the session cookie and can be used for any other security related needs by extensions or your application."""
    PERMANENT_SESSION_LIFETIME = os.getenv("PERMANENT_SESSION_LIFETIME_DAYS", 7)
    """Lifetime of a permanent session."""
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URL",
        f"sqlite:///{basedir / 'db.sqlite3'}",
    )
    """Database URI that should be used for the connection."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    """This is just here to suppress a warning from SQLAlchemy as it will soon be removed and we don't need it."""
