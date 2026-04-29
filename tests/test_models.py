# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>

import datetime

import pytest

from app.db.models.sequences import Sequence, Task
from app.db.models.templates import SequenceTemplate, TaskTemplate
from app.db.models.users import User


def test_user_full_name_column_property(user: User) -> None:
    assert user.full_name == "Alice Anderson"


def test_user_password_is_hashed(user: User) -> None:
    assert user.hashed_password == "s3cret-pw"
    assert str(user.hashed_password) != "s3cret-pw"


def test_user_find_by_id(user: User) -> None:
    found = User.find_by_id(user.id)
    assert found is not None
    assert found.username == "alice"


def test_sequence_template_cascade_delete_tasks(user: User) -> None:
    tmpl = SequenceTemplate(
        name="Morning",
        description="Morning routine",
        user_id=user.id,
    )
    tmpl.upsert()
    TaskTemplate(
        name="Brush teeth",
        description="2 min",
        sequence_template_id=tmpl.id,
        user_id=user.id,
    ).upsert()
    TaskTemplate(
        name="Coffee",
        description="brew",
        sequence_template_id=tmpl.id,
        user_id=user.id,
    ).upsert()

    assert len(tmpl.tasks) == 2
    tmpl.delete()
    assert TaskTemplate.query.count() == 0


@pytest.mark.xfail(
    reason="Pending user contribution: assert task_count, completed_task_count, tasks_summary",
    strict=False,
)
def test_sequence_task_count_properties(user: User) -> None:
    tmpl = SequenceTemplate(name="T", description="d", user_id=user.id)
    tmpl.upsert()
    seq = Sequence(
        name="Day 1",
        description="run",
        template_id=tmpl.id,
        user_id=user.id,
    )
    seq.upsert()
    Task(
        name="t1",
        description="d",
        sequence_id=seq.id,
        user_id=user.id,
        date_completed=datetime.datetime.utcnow(),
    ).upsert()
    Task(
        name="t2",
        description="d",
        sequence_id=seq.id,
        user_id=user.id,
        date_completed=None,
    ).upsert()

    # TODO(user): assert correct values for task_count, completed_task_count,
    # and tasks_summary on `seq`. Trade-off: do you want to assert exact
    # emoji strings in tasks_summary (brittle if UI changes) or just count
    # ✔️/❌ occurrences (resilient)? Implement 3-4 assertions below.
    msg = "user contribution: see TODO above"
    raise NotImplementedError(msg)
