# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
# Copyright (C) 2024 <hasansezertasan@gmail.com>
from flask_admin import Admin

from .db import Sequence, SequenceTemplate, db
from .views import AboutView as AboutView
from .views import ChangePasswordView as ChangePasswordView
from .views import EditProfileView as EditProfileView
from .views import IndexView as IndexView
from .views import LoginView as LoginView
from .views import LogoutView as LogoutView
from .views import RegisterView as RegisterView
from .views import SequenceTemplateView as SequenceTemplateView
from .views import SequenceView as SequenceView

admin = Admin(
    name="Not Just a Todo App",
    index_view=IndexView(
        name="Home",
        url="/",
        category="Home",
        template="/admin/index.html",
    ),
    template_mode="bootstrap4",
    endpoint="admin",
    base_template="admin/master.html",
)
admin.add_category(name="Home")
admin.add_view(
    AboutView(
        name="About",
        url="/about",
        endpoint="about",
    )
)
admin.add_view(
    LoginView(
        name="Login",
        url="/login",
        endpoint="login",
    )
)
admin.add_view(
    RegisterView(
        name="Register",
        url="/register",
        endpoint="register",
    )
)
admin.add_view(
    EditProfileView(
        name="Edit Profile",
        url="/edit-profile",
        endpoint="edit-profile",
    )
)
admin.add_view(
    ChangePasswordView(
        name="Change Password",
        url="/change-password",
        endpoint="change-password",
    )
)
admin.add_view(
    LogoutView(
        name="Logout",
        url="/logout",
        endpoint="logout",
    )
)
admin.add_view(
    SequenceTemplateView(
        model=SequenceTemplate,
        session=db.session,
        name="Sequence Templates",
        url="/sequence-template",
        endpoint="sequence-template",
    )
)
admin.add_view(
    SequenceView(
        model=Sequence,
        session=db.session,
        name="Sequences",
        url="/sequence",
        endpoint="sequence",
    )
)
