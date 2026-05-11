# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Flask extension singletons.

Declared at module level without an app — bound to a Flask app instance
inside the application factory via ``init_app()``. This pattern keeps
extensions importable from anywhere (including models, views, CLI) and
allows multiple Flask apps in the same process (tests, multi-tenant).
"""

from flask_bootstrap import Bootstrap4
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_static_digest import FlaskStaticDigest
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
migrate = Migrate()
bootstrap = Bootstrap4()
csrf = CSRFProtect()
compress = Compress()
static_digest = FlaskStaticDigest()
limiter = Limiter(key_func=get_remote_address)

login_manager.session_protection = "strong"


@login_manager.user_loader
def _load_user(user_id):
    from app.db.models.users import User

    return User.find_by_id(user_id)
