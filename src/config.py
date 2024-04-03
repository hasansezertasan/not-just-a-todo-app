# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
# Copyright (C) 2024 <hasansezertasan@gmail.com>
import os
from pathlib import Path

basedir = Path(__name__).resolve().parent


class FlaskConfig:
    # [Configuration Handling — Flask Documentation (2.3.x)](https://flask.palletsprojects.com/en/2.3.x/config/)
    SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "super-secret")
    PERMENANT_SESSION_LIFETIME = os.getenv("PERMANENT_SESSION_LIFETIME_DAYS", 7)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URL", f"sqlite:///{basedir / 'db.sqlite3'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
