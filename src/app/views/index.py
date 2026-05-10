# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
from flask import flash, redirect, request, url_for
from flask_admin import AdminIndexView, expose
from flask_login import login_user, logout_user

from app.db.models.users import User
from app.forms import LoginForm, RegisterForm
from app.observability import metrics as domain_metrics
from app.services import auth as auth_service


def _bump(name: str, **labels: str) -> None:
    """Increment a domain counter if metrics are enabled, no-op otherwise."""
    counter = domain_metrics.get(name)
    if counter is None:
        return
    (counter.labels(**labels) if labels else counter).inc()


class IndexView(AdminIndexView):
    @expose(url="/", methods=["GET"])
    def index(self):
        self.extra_js = []
        return self.render("admin/index.html")

    @expose("/login/", methods=["GET", "POST"])
    def login_view(self):
        """Login view."""
        self.extra_js = [
            url_for(
                "static",
                filename="vendor/bootstrap-show-password/bootstrap-show-password.min.js",
            ),
        ]
        form = LoginForm()
        if request.method == "POST" and form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = User.query.filter_by(username=username).first()

            if user and auth_service.is_locked(user):
                _bump("login_attempts", result="locked")
                flash(
                    "Account temporarily locked due to too many failed attempts.",
                    "danger",
                )
                return self.render(template="admin/form-page.html", form=form)

            if user and user.hashed_password == password:
                auth_service.record_successful_login(user)
                login_user(user)
                _bump("login_attempts", result="success")
                flash("You are now logged in.", "success")
                return redirect(url_for(".index"))

            if user is not None:
                # Only count attempts against known users — prevents the
                # lockout counter from being weaponized to enumerate usernames.
                auth_service.record_failed_login(user)
            _bump("login_attempts", result="invalid")
            flash("Invalid username or password.", "danger")
        return self.render(template="admin/form-page.html", form=form)

    @expose("/logout/", methods=["GET"])
    def logout_view(self):
        """Logout view."""
        logout_user()
        flash("You are now logged out.", "success")
        return redirect(url_for(".index"))

    @expose("/register/", methods=["GET", "POST"])
    def register_view(self):
        """Register view."""
        self.extra_js = [
            url_for(
                "static",
                filename="vendor/bootstrap-show-password/bootstrap-show-password.min.js",
            ),
        ]
        form = RegisterForm()
        if request.method == "POST" and form.validate_on_submit():
            username = form.username.data
            found = User.query.filter_by(username=username).first()
            if found:
                _bump("registrations", result="duplicate_username")
                flash("Username already exists.", "danger")
                return self.render(template="admin/form-page.html", form=form)

            user = User(
                username=username,
                hashed_password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
            )
            user.upsert()
            _bump("registrations", result="success")
            flash("Thank you for registering. Please login.", "success")
            return redirect(url_for(".login_view"))
        return self.render(template="admin/form-page.html", form=form)

    def is_visible(self) -> bool:
        return False
