# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
# Copyright (C) 2024 <hasansezertasan@gmail.com>
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


class RegisterForm(FlaskForm):
    username = StringField(
        label="Username",
        validators=[DataRequired()],
        description="Enter your username.",
        render_kw={"class": "form-control", "placeholder": "Username"},
    )
    password = PasswordField(
        label="Password",
        validators=[DataRequired()],
        description="Enter your password.",
        render_kw={
            "class": "form-control",
            "placeholder": "Password",
            "data-toggle": "password",
            "data-placement": "before",
            "data-message": "Show/Hide Password",
            "data-eye-open-class": "fa-toggle-off",
            "data-eye-close-class": "fa-toggle-on",
        },
    )
    password_again = PasswordField(
        label="Password Again",
        validators=[DataRequired(), EqualTo("password")],
        description="Enter your password again.",
        render_kw={
            "class": "form-control",
            "placeholder": "Password Again",
            "data-toggle": "password",
            "data-placement": "before",
            "data-message": "Show/Hide Password",
            "data-eye-open-class": "fa-toggle-off",
            "data-eye-close-class": "fa-toggle-on",
        },
    )
    first_name = StringField(
        label="First Name",
        validators=[DataRequired()],
        description="Enter your first name.",
        render_kw={"class": "form-control", "placeholder": "First Name"},
    )
    last_name = StringField(
        label="Last Name",
        validators=[DataRequired()],
        description="Enter your last name.",
        render_kw={"class": "form-control", "placeholder": "Last Name"},
    )
    email = EmailField(
        label="E-mail",
        validators=[DataRequired(), Email()],
        description="Enter your e-mail.",
        render_kw={"class": "form-control", "placeholder": "E-mail"},
    )
    submit = SubmitField(
        label="Sign Up",
        description="Click to sign up.",
        render_kw={"class": "btn btn-lg btn-dark btn-block form-control"},
    )


class LoginForm(FlaskForm):
    username = StringField(
        label="Username",
        validators=[DataRequired()],
        description="Enter your username.",
        render_kw={"class": "form-control", "placeholder": "Username"},
    )
    password = PasswordField(
        label="Password",
        validators=[DataRequired()],
        description="Enter your password.",
        render_kw={
            "class": "form-control",
            "placeholder": "Password",
            "data-toggle": "password",
            "data-placement": "before",
            "data-message": "Show/Hide Password",
            "data-eye-open-class": "fa-toggle-off",
            "data-eye-close-class": "fa-toggle-on",
        },
    )
    submit = SubmitField(
        label="Sign In",
        description="Click to sign in.",
        render_kw={"class": "btn btn-lg btn-dark btn-block form-control"},
    )


class ChangePasswordForm(FlaskForm):
    password = PasswordField(
        label="Password",
        validators=[DataRequired()],
        description="Enter your password.",
        render_kw={
            "class": "form-control",
            "placeholder": "Password",
            "data-toggle": "password",
            "data-placement": "before",
            "data-message": "Show/Hide Password",
            "data-eye-open-class": "fa-toggle-off",
            "data-eye-close-class": "fa-toggle-on",
        },
    )
    new_password = PasswordField(
        label="New Password",
        validators=[DataRequired()],
        description="Enter your new password.",
        render_kw={
            "class": "form-control",
            "placeholder": "New password",
            "data-toggle": "password",
            "data-placement": "before",
            "data-message": "Show/Hide Password",
            "data-eye-open-class": "fa-toggle-off",
            "data-eye-close-class": "fa-toggle-on",
        },
    )
    new_password_again = PasswordField(
        label="New Password Again",
        validators=[DataRequired(), EqualTo("new_password")],
        description="Enter your new password again.",
        render_kw={
            "class": "form-control",
            "placeholder": "New password again",
            "data-toggle": "password",
            "data-placement": "before",
            "data-message": "Show/Hide Password",
            "data-eye-open-class": "fa-toggle-off",
            "data-eye-close-class": "fa-toggle-on",
        },
    )
    submit = SubmitField(
        label="Change Password",
        description="Click to change password.",
        render_kw={"class": "btn btn-lg btn-dark btn-block form-control"},
    )


class EditProfileForm(FlaskForm):
    first_name = StringField(
        label="First Name",
        validators=[DataRequired()],
        description="Enter your first name.",
        render_kw={"class": "form-control", "placeholder": "First Name"},
    )
    last_name = StringField(
        label="Last Name",
        validators=[DataRequired()],
        description="Enter your last name.",
        render_kw={"class": "form-control", "placeholder": "Last Name"},
    )
    email = EmailField(
        label="E-mail",
        validators=[DataRequired(), Email()],
        description="Enter your e-mail.",
        render_kw={"class": "form-control", "placeholder": "E-mail"},
    )
    submit = SubmitField(
        label="Update Profile",
        description="Click to update profile.",
        render_kw={"class": "btn btn-lg btn-dark btn-block form-control"},
    )
