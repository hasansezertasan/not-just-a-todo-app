import datetime
import json
import os
import random

import typer

from src.app import app as server
from src.db import (
    Sequence,
    SequenceTemplate,
    Task,
    TaskTemplate,
    User,
    db,
)

basedir = os.path.abspath(os.path.dirname(__name__))


app = typer.Typer(
    name="Not Just a Todo App",
    add_completion=False,
    no_args_is_help=True,
)


@app.command(help="Create database")
def create_database():
    """
    Create database

    Usage:
        python toolbox create-database
    """
    with server.app_context():
        db.create_all()


@app.command(help="Clear database", short_help="Clear database")
def clear_database(
    verify: bool = typer.Option(
        False,
        help="Verify that you want to clear the database",
        prompt="Are you sure you want to clear the database?",
        is_flag=True,
    ),
):
    """
    Clear database

    Usage:
        python app.py clear-database
    """
    if not verify:
        typer.echo("Please verify that you want to clear the database.")
        return
    with server.app_context():
        db.session.commit()
        db.drop_all()


@app.command(help="Seed Users Table")
def seed_users_table():
    """
    Seed Users Table

    Usage:
        python toolbox seed-users-table
    """
    path = os.path.join(basedir, "tests", "assets", "users.json")
    with open(path, "r", encoding="utf-8") as f:
        users = json.load(f)
    for idx, user in enumerate(users):
        users[idx]["hashed_password"] = user["password"]
        del users[idx]["password"]
    with server.app_context():
        db.session.bulk_insert_mappings(User, users)
        db.session.commit()


@app.command(help="Seed Sequence Templates Table")
def seed_sequence_templates_table():
    """
    Seed Sequence Templates Table

    Usage:
        python toolbox seed-sequence-templates-table
    """
    path = os.path.join(basedir, "tests", "assets", "sequences.json")
    with open(path, "r", encoding="utf-8") as f:
        sequence_templates = json.load(f)
    with server.app_context():
        for sequence_template in sequence_templates:
            tasks = sequence_template.pop("tasks")
            username = sequence_template.pop("user")
            user = User.query.filter_by(username=username).first()
            sequence = SequenceTemplate(**sequence_template, user_id=user.id)
            for task in tasks:
                sequence.tasks.append(TaskTemplate(**task, user_id=user.id))
            db.session.add(sequence)
        db.session.commit()


if __name__ == "__main__":
    app()
