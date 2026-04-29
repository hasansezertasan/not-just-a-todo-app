# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
from __future__ import annotations

import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.models.base import Base
from app.db.models.mixins import StandardMixin, UserPropertyMixin


class Sequence(Base, StandardMixin, UserPropertyMixin):
    __tablename__ = "sequence"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    template_id: Mapped[int] = mapped_column(ForeignKey("sequence_template.id"))
    tasks: Mapped[list[Task]] = relationship(
        back_populates="sequence",
        cascade="all, delete-orphan",
    )

    @property
    def task_count(self):
        return len(self.tasks)

    @property
    def completed_task_count(self):
        completed_tasks = [
            task for task in self.tasks if task.date_completed is not None
        ]
        return len(completed_tasks)

    @property
    def tasks_summary(self):
        return [
            f"{'✔️' if task.date_completed else '❌'} {task.name}" for task in self.tasks
        ]


class Task(Base, StandardMixin, UserPropertyMixin):
    __tablename__ = "task"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    sequence_id: Mapped[int] = mapped_column(ForeignKey("sequence.id"))
    sequence: Mapped[Sequence] = relationship(back_populates="tasks")
    date_completed: Mapped[datetime.datetime | None]
