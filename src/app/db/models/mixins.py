# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import (
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)

from app.db.models.base import db

if TYPE_CHECKING:
    from app.db.models.users import User


class StandardMixin:
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    date_created: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC),
        server_default=func.now(),
        index=True,
    )
    date_updated: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
        server_default=func.now(),
        server_onupdate=func.now(),
        index=True,
    )

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    def upsert(self) -> None:
        db.session.add(self)
        db.session.commit()
        db.session.refresh(self)

    def delete(self) -> None:
        db.session.delete(self)
        db.session.commit()


class UserPropertyMixin:
    @declared_attr
    def user_id(self) -> Mapped[int]:
        return mapped_column(ForeignKey("user.id"))

    @declared_attr
    def user(self) -> Mapped[User]:
        return relationship("User")
