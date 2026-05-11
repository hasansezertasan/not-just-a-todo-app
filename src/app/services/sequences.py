# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Sequence + Task domain operations."""

import datetime

from app.db.models.sequences import Sequence, Task
from app.db.models.templates import SequenceTemplate


def instantiate_from_template(*, template_id: int, user_id: int) -> Sequence:
    """Materialize a `Sequence` (with `Task` rows) from a `SequenceTemplate`.

    Pure domain operation: takes IDs, returns the saved Sequence. Views
    only need to provide the current user; no Flask request context here.
    """
    template = SequenceTemplate.find_by_id(template_id)
    sequence = Sequence(
        name=template.name,
        description=template.description,
        template_id=template_id,
        user_id=user_id,
    )
    for task_template in template.tasks:
        sequence.tasks.append(
            Task(
                name=task_template.name,
                description=task_template.description,
                user_id=user_id,
            )
        )
    sequence.upsert()
    return sequence


def mark_task_completed(*, task_id: int) -> Task | None:
    """Stamp `date_completed` on a Task and persist. Returns None if missing."""
    task = Task.query.filter(Task.id == task_id).first()
    if task is None:
        return None
    task.date_completed = datetime.datetime.now(datetime.UTC)
    task.upsert()
    return task


def get_sequence(sequence_id: int) -> Sequence | None:
    return Sequence.find_by_id(sequence_id)
