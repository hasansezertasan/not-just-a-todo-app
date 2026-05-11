# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Flask CLI commands.

Commands are grouped under `flask seed ...` via ``flask.cli.AppGroup``.
Grouping keeps the CLI surface scannable as new fixtures are added —
``flask --help`` shows one ``seed`` entry instead of N flat commands.
"""

import json

from flask.cli import AppGroup, with_appcontext

from app.config import FIXTURES_DIR
from app.db.models.base import db
from app.db.models.templates import SequenceTemplate, TaskTemplate
from app.db.models.users import User

seed = AppGroup("seed", help="Seed the database with fixture data.")


@seed.command("users", help="Seed the users table from fixtures/users.json.")
@with_appcontext
def seed_users() -> None:
    """Usage: flask seed users."""
    path = FIXTURES_DIR / "users.json"
    with path.open(encoding="utf-8") as f:
        users = json.load(f)
    for idx, user in enumerate(users):
        users[idx]["hashed_password"] = user["password"]
        del users[idx]["password"]
    db.session.bulk_insert_mappings(User, users)
    db.session.commit()


@seed.command(
    "sequences",
    help="Seed the sequence_template + task_template tables.",
)
@with_appcontext
def seed_sequences() -> None:
    """Usage: flask seed sequences."""
    path = FIXTURES_DIR / "sequences.json"
    with path.open(encoding="utf-8") as f:
        sequence_templates = json.load(f)
    for sequence_template in sequence_templates:
        tasks = sequence_template.pop("tasks")
        username = sequence_template.pop("user")
        user = User.query.filter_by(username=username).first()
        sequence = SequenceTemplate(**sequence_template, user_id=user.id)
        for task in tasks:
            sequence.tasks.append(TaskTemplate(**task, user_id=user.id))
        db.session.add(sequence)
    db.session.commit()
