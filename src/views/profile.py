from flask import redirect, request, url_for
from flask_admin import BaseView, expose
from flask_login import current_user, login_required, login_user, logout_user

from src.db import User
from src.forms import ChangePasswordForm, EditProfileForm, LoginForm, RegisterForm

from .mixins import AnonymousMixin, MemberMixin


class LoginView(AnonymousMixin, BaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        if current_user.is_authenticated:
            return redirect(url_for("admin.index"))
        form = LoginForm()
        if request.method == "POST" and form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = User.query.filter_by(username=username).first()
            if user and user.hashed_password == password:
                login_user(user)
                return redirect(url_for("admin.index"))
            else:
                return self.render(
                    "admin/form-page.html",
                    form=form,
                    error="Invalid username or password.",
                )
        return self.render(
            "admin/form-page.html",
            form=form,
        )


class RegisterView(AnonymousMixin, BaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        if current_user.is_authenticated:
            return redirect(url_for("admin.index"))
        form = RegisterForm()
        if request.method == "POST" and form.validate_on_submit():
            username = form.username.data
            found = User.query.filter_by(username=username).first()
            if found:
                return self.render(
                    "admin/register.html",
                    form=form,
                    error="Username already exists.",
                )

            user = User(
                username=username,
                hashed_password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
            )
            user.upsert()
            return self.render(
                "admin/form-page.html",
                form=form,
                error="Thank you for registering. Please login.",
            )
        return self.render("admin/form-page.html", form=form)


class LogoutView(MemberMixin, BaseView):
    @expose("/", methods=["GET"])
    def index(self):
        logout_user()
        return redirect(url_for("admin.index"))


class EditProfileView(MemberMixin, BaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        print(self.name)
        form = EditProfileForm(obj=current_user._get_current_object())
        if request.method == "POST" and form.validate_on_submit():
            user: User = User.query.filter_by(username=current_user.username).first()
            if user:
                current_user.first_name = form.first_name.data
                current_user.last_name = form.last_name.data
                current_user.email = form.email.data
                current_user.upsert()
                return self.render(
                    "admin/form-page.html",
                    form=form,
                    error="Profile updated.",
                )
            return self.render(
                "admin/form-page.html",
                form=form,
                error="User not found.",
            )
        return self.render(
            "admin/form-page.html",
            form=form,
        )


class ChangePasswordView(MemberMixin, BaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        form = ChangePasswordForm()
        if request.method == "POST" and form.validate_on_submit():
            if form.new_password.data != form.new_password_again.data:
                return self.render(
                    "admin/form-page.html",
                    form=form,
                    error="New passwords do not match.",
                )
            user: User = User.query.filter_by(username=current_user.username).first()
            if user and user.hashed_password == form.password.data:
                user.hashed_password = form.new_password.data
                user.upsert()
                logout_user()
                return redirect(url_for("admin.index"))
            return self.render(
                "admin/form-page.html",
                form=form,
                error="Invalid password.",
            )
        return self.render(
            "admin/form-page.html",
            form=form,
        )
