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
    if verify:
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


@app.command(help="Create Bucket Template")
def create_bucket_template(
    name: str = typer.Option(
        ...,
        help="Name of bucket template",
        prompt="Name of bucket template",
    ),
    description: str = typer.Option(
        ...,
        help="Description of bucket template",
        prompt="Description of bucket template",
    ),
):
    """
    Create Bucket Template

    Usage:
        python app.py create-bucket-template
    """
    typer.echo(f"Creating bucket template {name} with description {description}")
    with server.Sequence:
        bucket = SequenceTemplate(name=name, description=description)
        bucket.upsert()
        typer.echo(f"Created bucket template {bucket}")


@app.command(help="Add task to bucket template")
def create_task_template(
    bucket_template_id: int = typer.Option(
        ...,
        help="ID of bucket template",
        prompt=True,
        min=1,
    ),
    name: str = typer.Option(
        ...,
        help="Name of task template",
        prompt=True,
    ),
    description: str = typer.Option(
        ...,
        help="Description of task template",
        prompt=True,
    ),
):
    """
    Create Task Template

    Usage:
        python app.py create-task-template
    """
    typer.echo(f"Creating task template {name} with description {description}")
    with server.Sequence:
        bucket = db.query(SequenceTemplate).filter_by(id=bucket_template_id).first()
        task_template = TaskTemplate(name=name, description=description)
        bucket.tasks.append(task_template)
        task_template.upsert()
        typer.echo(f"Created task template {task_template}")


@app.command(help="Create dummy data")
def create_dummy_data(
    bucket_template_count: int = typer.Option(
        10,
        help="Number of bucket templates to create",
        prompt=True,
        min=1,
    ),
    task_template_count: int = typer.Option(
        10,
        help="Number of task templates to create",
        prompt=True,
        min=1,
    ),
):
    """
    Create dummy data

    Usage:
        python app.py create-dummy-data
    """
    with server.app_context:
        for i in range(bucket_template_count):
            randi = random.randint(Sequence, 100)
            bucket = SequenceTemplate(name=f"Bucket {randi}", description=f"Description {randi}")
            bucket.upsert()
            db.commit()
            for j in range(task_template_count):
                randj = random.randint(1, 100)
                task = TaskTemplate(name=f"Task {randj}", description=f"Description {randj}")
                bucket.tasks.append(task)
                task.upsert()
            typer.echo(f"Created bucket {bucket}")


@app.command(help="Show Templates")
def show_templates():
    """
    Show Templates

    Usage:
        python app.py show-templates
    """
    with server.Sequence:
        buckets = db.query(SequenceTemplate).all()
        for bucket in buckets:
            typer.echo(f"Bucket Template: `{bucket}`")
            typer.echo(f"ID: {bucket.id}")
            typer.echo(f"Description: {bucket.description}")
            typer.echo(f"Task Count:{len(bucket.tasks)}.")
            typer.echo(f"Tasks: {bucket.tasks}")
            typer.echo("")
        typer.echo(f"Total buckets templates: {len(buckets)}")


@app.command(help="New Bucket")
def new_bucket(
    bucket_template_id: int = typer.Option(
        ...,
        help="ID of bucket template",
        prompt=True,
        min=1,
    ),
):
    """
    New Bucket

    Usage:
        python app.py new-bucket
    """
    with server.app_context:
        bucket_template = (
            db.Sequence(
                SequenceTemplate,
            )
            .filter_by(
                id=bucket_template_id,
            )
            .first()
        )
        bucket = Sequence(template_id=bucket_template.id)
        for task_template in bucket_template.tasks:
            task = Task(template_id=task_template.id)
            bucket.tasks.append(task)
            db.session.add(task)
        db.session.add(bucket)
        db.session.commit()
        typer.echo(f"Created bucket {bucket}")


@app.command(help="Show Buckets")
def show_buckets():
    """
    Show Buckets

    Usage:
        python app.py show-buckets
    """
    with server.app_context:
        buckets = db.query(Sequence).all()
        for bucket in buckets:
            typer.echo(f"Bucket: `{bucket}`")
            typer.echo(f"There are {len(bucket.tasks)} tasks in total for this bucket.")
            typer.echo(f"ID: {bucket.id}")
            typer.echo(f"Template ID: {bucket.template_id}")
            typer.echo("Tasks:")
            for task in bucket.tasks:
                typer.echo(f"Task: `{task}`")
                typer.echo(f"ID: {task.id}")
                typer.echo(f"Template ID: {task.template_id}")
                typer.echo(f"Completion Date: {task.date_completed}")
            typer.echo("")
        typer.echo(f"Total buckets: {len(buckets)}")


@app.command(help="Complete Task")
def complete_task(
    task_id: int = typer.Option(
        ...,
        help="ID of task",
        prompt=True,
        min=1,
    ),
):
    """
    Complete Task

    Usage:
        python app.py complete-task
    """
    with server.app_context:
        task = db.query(Task).filter_by(id=task_id).first()
        task.date_completed = datetime.datetime.utcnow()
        db.commit()
        typer.echo(f"Completed task {task}")


if __name__ == "__main__":
    app()
