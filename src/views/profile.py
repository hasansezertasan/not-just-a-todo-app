# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
# Copyright (C) 2024 <hasansezertasan@gmail.com>
from flask import flash, redirect, request, url_for
from flask_admin import BaseView, expose
from flask_login import current_user, logout_user

from src.forms import ChangePasswordForm, EditProfileForm

from .mixins import InvisibleMixin, MemberMixin


class EditProfileView(MemberMixin, InvisibleMixin, BaseView):
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


class ChangePasswordView(MemberMixin, InvisibleMixin, BaseView):
    extra_js = [
        "https://unpkg.com/bootstrap-show-password@1.2.1/dist/bootstrap-show-password.min.js"
    ]

    @expose("/", methods=["GET", "POST"])
    def index(self):
        form = ChangePasswordForm()
        if request.method == "POST" and form.validate_on_submit():
            if current_user.hashed_password == form.password.data:
                current_user.hashed_password = form.new_password.data
                current_user.upsert()
                logout_user()
                flash("Password changed successfully. Please login.", "success")
                return redirect(url_for(self.admin.endpoint + ".index"))
            flash("Invalid password.", "danger")
        return self.render("admin/form-page.html", form=form)
