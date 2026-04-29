# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_mixins import AllFeaturesMixin

db = SQLAlchemy()


class Base(db.Model, AllFeaturesMixin):  # type: ignore
    __abstract__ = True
