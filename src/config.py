import os

basedir = os.path.abspath(os.path.dirname(__name__))

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "super-secret")
PERMANENT_SESSION_LIFETIME_DAYS = os.getenv("PERMANENT_SESSION_LIFETIME_DAYS", 7)
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'db.sqlite3')}")


class FlaskConfig:
    # [Configuration Handling — Flask Documentation (2.3.x)](https://flask.palletsprojects.com/en/2.3.x/config/)
    SECRET_KEY = SESSION_SECRET_KEY
    PERMENANT_SESSION_LIFETIME = PERMANENT_SESSION_LIFETIME_DAYS
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
