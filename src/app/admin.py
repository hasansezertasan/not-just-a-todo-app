# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
from flask_admin import Admin
from flask_admin.theme import Bootstrap4Theme

from app.db.models.base import db
from app.db.models.sequences import Sequence
from app.db.models.templates import SequenceTemplate
from app.views import (
    AboutView,
    ChangePasswordView,
    EditProfileView,
    IndexView,
    SequenceTemplateView,
    SequenceView,
)

admin = Admin(
    name="Not Just a TODO App",
    index_view=IndexView(
        name="Home",
        url="/",
        category="Home",
        template="/admin/index.html",
    ),
    theme=Bootstrap4Theme(base_template="admin/master.html"),
    endpoint="admin",
)
admin.add_category(name="Home")
admin.add_view(
    AboutView(
        name="About",
        url="/about",
        endpoint="about",
    ),
)
admin.add_view(
    EditProfileView(
        name="Edit Profile",
        url="/edit-profile",
        endpoint="edit-profile",
    ),
)
admin.add_view(
    ChangePasswordView(
        name="Change Password",
        url="/change-password",
        endpoint="change-password",
    ),
)
admin.add_view(
    SequenceTemplateView(
        model=SequenceTemplate,
        session=db,
        name="Sequence Templates",
        url="/sequence-template",
        endpoint="sequence-template",
    ),
)
admin.add_view(
    SequenceView(
        model=Sequence,
        session=db,
        name="Sequences",
        url="/sequence",
        endpoint="sequence",
    ),
)
