from flask_admin import Admin

from .db import SequenceTemplate, db, Sequence
from .views.about import AboutView
from .views.index import IndexView
from .views.profile import ChangePasswordView, EditProfileView, LoginView, LogoutView, RegisterView
from .views.sequences import SequenceTemplateView, SequenceView

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
)
admin.add_category(name="Profile")
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
        category="Profile",
    )
)
admin.add_view(
    RegisterView(
        name="Register",
        url="/register",
        endpoint="register",
        category="Profile",
    )
)
admin.add_view(
    EditProfileView(
        name="Edit Profile",
        url="/edit-profile",
        endpoint="edit-profile",
        category="Profile",
    )
)
admin.add_view(
    ChangePasswordView(
        name="Change Password",
        url="/change-password",
        endpoint="change-password",
        category="Profile",
    )
)
admin.add_view(
    LogoutView(
        name="Logout",
        url="/logout",
        endpoint="logout",
        category="Profile",
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

