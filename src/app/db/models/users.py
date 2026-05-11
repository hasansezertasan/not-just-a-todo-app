# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
import datetime

from flask_login import UserMixin
from sqlalchemy.orm import (
    Mapped,
    column_property,
    mapped_column,
)
from sqlalchemy_utils import EmailType, PasswordType

from app.db.models.base import Base
from app.db.models.mixins import StandardMixin


class User(Base, UserMixin, StandardMixin):
    __tablename__ = "user"
    __repr_attrs__ = ["username"]
    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column(
        PasswordType(
            # argon2 first → new hashes use argon2; bcrypt kept so existing
            # rows still verify and get rehashed-on-login transparently.
            schemes=["argon2", "bcrypt"],
            deprecated=["auto"],
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
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    # Lockout state — see app.services.auth
    failed_login_count: Mapped[int] = mapped_column(default=0, server_default="0")
    locked_until: Mapped[datetime.datetime | None] = mapped_column(default=None)
