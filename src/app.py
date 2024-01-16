from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_migrate import Migrate

from src.config import FlaskConfig
from src.db import User, db

from .admin import admin

app = Flask(__name__)
app.config.from_object(FlaskConfig)
login_manager = LoginManager()
migrate = Migrate()
bootstrap = Bootstrap5(app)

# Initialize Extensions
admin.init_app(app)
migrate.init_app(app=app, db=db)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login.index"


# Login Manager
@login_manager.user_loader
def load_user(user_id):
    return User.find_by_id(user_id)
