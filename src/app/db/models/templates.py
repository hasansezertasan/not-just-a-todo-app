# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.models.base import Base
from app.db.models.mixins import StandardMixin, UserPropertyMixin


class SequenceTemplate(Base, StandardMixin, UserPropertyMixin):
    __tablename__ = "sequence_template"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    tasks: Mapped[list[TaskTemplate]] = relationship(
        back_populates="sequence_template",
        cascade="all, delete-orphan",
    )
    # TODO: Add a column to set a time limit for the sequence


class TaskTemplate(Base, StandardMixin, UserPropertyMixin):
    __tablename__ = "task_template"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    sequence_template_id: Mapped[int] = mapped_column(
        ForeignKey("sequence_template.id"),
    )
    sequence_template: Mapped[SequenceTemplate] = relationship(back_populates="tasks")
