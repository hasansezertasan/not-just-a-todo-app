# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_login import LoginManager
from flask_migrate import Migrate

from app import commands
from app.admin import admin
from app.config import FlaskConfig
from app.db.models.base import db
from app.db.models.users import User

app = Flask(__name__)
app.config.from_object(FlaskConfig)  # Update app configuration with FlaskConfig class.
login_manager = LoginManager()
migrate = Migrate()
bootstrap = Bootstrap4(app)

# Register CLI Commands
app.cli.add_command(commands.create_database)
app.cli.add_command(commands.clear_database)
app.cli.add_command(commands.seed_users_table)
app.cli.add_command(commands.seed_sequence_templates_table)

# Initialize Extensions
admin.init_app(app)
migrate.init_app(app=app, db=db)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = admin.index_view.endpoint + ".login_view"


# Login Manager
@login_manager.user_loader
def load_user(user_id):
    return User.find_by_id(user_id)
