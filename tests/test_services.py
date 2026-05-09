# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Service-layer tests — exercise app.services without the HTTP surface."""

from typing import TYPE_CHECKING

from app.db.models.sequences import Sequence, Task
from app.db.models.templates import SequenceTemplate, TaskTemplate
from app.services import sequences as sequence_service

if TYPE_CHECKING:
    from app.db.models.users import User


def _seed_template(user: User) -> SequenceTemplate:
    tmpl = SequenceTemplate(
        name="Morning",
        description="Morning routine",
        user_id=user.id,
    )
    tmpl.upsert()
    for name in ("Brush teeth", "Coffee"):
        TaskTemplate(
            name=name,
            description="...",
            sequence_template_id=tmpl.id,
            user_id=user.id,
        ).upsert()
    return tmpl


def test_instantiate_from_template_creates_sequence_with_tasks(user: User) -> None:
    tmpl = _seed_template(user)

    sequence = sequence_service.instantiate_from_template(
        template_id=tmpl.id, user_id=user.id
    )

    assert isinstance(sequence, Sequence)
    assert sequence.template_id == tmpl.id
    assert sequence.user_id == user.id
    assert len(sequence.tasks) == 2
    assert {t.name for t in sequence.tasks} == {"Brush teeth", "Coffee"}


def test_get_sequence_returns_persisted_row(user: User) -> None:
    tmpl = _seed_template(user)
    seq = sequence_service.instantiate_from_template(
        template_id=tmpl.id, user_id=user.id
    )

    fetched = sequence_service.get_sequence(seq.id)
    assert fetched is not None
    assert fetched.id == seq.id


def test_mark_task_completed_stamps_date_completed(user: User) -> None:
    tmpl = _seed_template(user)
    seq = sequence_service.instantiate_from_template(
        template_id=tmpl.id, user_id=user.id
    )
    task_id = seq.tasks[0].id

    completed = sequence_service.mark_task_completed(task_id=task_id)
    assert completed.id == task_id
    assert completed.date_completed is not None

    # Re-fetch to confirm persistence.
    refetched = Task.query.filter(Task.id == task_id).one()
    assert refetched.date_completed is not None
