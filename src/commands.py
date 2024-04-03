# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
# Copyright (C) 2024 <hasansezertasan@gmail.com>
import json

import click
from flask.cli import with_appcontext

from src.config import basedir
from src.db import SequenceTemplate, TaskTemplate, User, db


@click.command(help="Create database")
@with_appcontext
def create_database():
    """Create database

    Usage:
        flask create-database
    """
    db.create_all()


@click.command(help="Clear database")
@click.option(
    "--verify",
    is_flag=True,
    default=False,
    help="Verify if you really want to clear the database",
    prompt="Do you really want to clear the database?",
)
@with_appcontext
def clear_database(verify: bool = False):
    """Clear database

    Usage:
        flask clear-database
    """
    if not verify:
        click.echo("Please verify that you want to clear the database.")
        return
    db.drop_all()
    click.echo("Database cleared")


@click.command(help="Seed Users Table")
@with_appcontext
def seed_users_table():
    """Seed Users Table

    Usage:
        flask seed-users-table
    """
    path = basedir / "tests" / "assets" / "users.json"
    with path.open(encoding="utf-8") as f:
        users = json.load(f)
    for idx, user in enumerate(users):
        users[idx]["hashed_password"] = user["password"]
        del users[idx]["password"]
    db.session.bulk_insert_mappings(User, users)
    db.session.commit()


@click.command(help="Seed Sequence Templates Table")
@with_appcontext
def seed_sequence_templates_table():
    """Seed Sequence Templates Table

    Usage:
        flask seed-sequence-templates-table
    """
    path = basedir / "tests" / "assets" / "sequences.json"
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
