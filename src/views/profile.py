from flask import flash, redirect, request, url_for
from flask_admin import BaseView, expose
from flask_login import current_user, login_user, logout_user

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
                flash("You are now logged in.", "success")
                return redirect(url_for("admin.index"))
            else:
                flash("Invalid username or password.", "danger")
        return self.render(template="admin/password-form-page.html", form=form)


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
                flash("Username already exists.", "danger")
                return self.render(template="admin/password-form-page.html", form=form)

            user = User(
                username=username,
                hashed_password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
            )
            user.upsert()
            flash("Thank you for registering. Please login.", "success")
            return redirect(url_for("login.index"))
        return self.render(template="admin/password-form-page.html", form=form)


class LogoutView(MemberMixin, BaseView):
    @expose("/", methods=["GET"])
    def index(self):
        logout_user()
        flash("You are now logged out.", "success")
        return redirect(url_for("admin.index"))


class EditProfileView(MemberMixin, BaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        form = EditProfileForm(obj=current_user._get_current_object())
        if request.method == "POST" and form.validate_on_submit():
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.email = form.email.data
            current_user.upsert()
            flash("Profile updated.", "success")
        return self.render(template="admin/form-page.html", form=form)


class ChangePasswordView(MemberMixin, BaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        form = ChangePasswordForm()
        if request.method == "POST" and form.validate_on_submit():
            if current_user.hashed_password == form.password.data:
                current_user.hashed_password = form.new_password.data
                current_user.upsert()
                logout_user()
                flash("Password changed successfully. Please login.", "success")
                return redirect(url_for("admin.index"))
            flash("Invalid password.", "danger")
        return self.render("admin/password-form-page.html", form=form)
