import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, column_property, declared_attr, mapped_column, relationship
from sqlalchemy_mixins import AllFeaturesMixin
from sqlalchemy_utils import EmailType, PasswordType

from ._types import UserRole

db = SQLAlchemy()


class StandardMixin:
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    date_created: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow,
        index=True,
    )
    date_updated: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        index=True,
    )

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    def upsert(self):
        db.session.add(self)
        db.session.commit()
        db.session.refresh(self)

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class User(db.Model, UserMixin, StandardMixin, AllFeaturesMixin):  # type: ignore
    __tablename__ = "user"
    __repr_attrs__ = ["username"]
    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column(
        PasswordType(
            schemes=[
                "bcrypt",
            ],
            deprecated=[
                "auto",
            ],
        ),
    )
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    full_name = column_property(first_name + " " + last_name)
    email: Mapped[str | None] = mapped_column(
        type_=EmailType,
        unique=True,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)


class UserPropertyMixin:
    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("user.id"))

    @declared_attr
    def user(cls) -> Mapped[User]:
        return relationship("User")


class SequenceTemplate(db.Model, StandardMixin, AllFeaturesMixin, UserPropertyMixin):  # type: ignore
    __tablename__ = "sequence_template"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    tasks: Mapped[list["TaskTemplate"]] = relationship(back_populates="sequence_template")
    # A column to set a time limit for the sequence


class TaskTemplate(db.Model, StandardMixin, AllFeaturesMixin, UserPropertyMixin):  # type: ignore
    __tablename__ = "task_template"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    sequence_template_id: Mapped[int] = mapped_column(ForeignKey("sequence_template.id"))
    sequence_template: Mapped[SequenceTemplate] = relationship(back_populates="tasks")


class Sequence(db.Model, StandardMixin, AllFeaturesMixin, UserPropertyMixin):  # type: ignore
    __tablename__ = "sequence"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    template_id: Mapped[int] = mapped_column(ForeignKey("sequence_template.id"))
    tasks: Mapped[list["Task"]] = relationship(back_populates="sequence", cascade="all, delete-orphan")

    @property
    def task_count(self):
        return len(self.tasks)

    @property
    def completed_task_count(self):
        completed_tasks = [task for task in self.tasks if task.date_completed is not None]
        return len(completed_tasks)

    @property
    def tasks_summary(self):
        return [f"{'✔️' if task.date_completed else '❌'} {task.name}" for task in self.tasks]


class Task(db.Model, StandardMixin, AllFeaturesMixin, UserPropertyMixin):  # type: ignore
    __tablename__ = "task"
    __repr_attrs__ = ["name"]
    name: Mapped[str]
    description: Mapped[str]
    sequence_id: Mapped[int] = mapped_column(ForeignKey("sequence.id"))
    sequence: Mapped[Sequence] = relationship(back_populates="tasks")
    date_completed: Mapped[datetime.datetime | None]
