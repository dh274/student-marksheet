from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    EmailField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Regexp,
)


def strip_value(value):
    return value.strip() if isinstance(value, str) else value


class RegistrationForm(FlaskForm):
    full_name = StringField(
        "Full name",
        filters=[strip_value],
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    email = EmailField(
        "Email address",
        filters=[strip_value],
        validators=[DataRequired(), Email(), Length(max=254)],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(
                min=12,
                max=128,
                message="Use a password between 12 and 128 characters.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = EmailField(
        "Email address",
        filters=[strip_value],
        validators=[DataRequired(), Email(), Length(max=254)],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Sign in")


class AdminLoginForm(FlaskForm):
    username = StringField(
        "Admin username", filters=[strip_value], validators=[DataRequired(), Length(max=254)]
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Admin sign in")


class ApplicationForm(FlaskForm):
    student_name = StringField(
        "Student name",
        filters=[strip_value],
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    registration_number = StringField(
        "Registration number",
        filters=[strip_value],
        validators=[
            DataRequired(),
            Length(min=1, max=40),
            Regexp(
                r"^[A-Za-z0-9/-]+$",
                message="Use letters, numbers, hyphens, or slashes only.",
            ),
        ],
    )
    department = StringField(
        "Department",
        filters=[strip_value],
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    semester = IntegerField(
        "Semester", validators=[DataRequired(), NumberRange(min=1, max=12)]
    )
    examination_year = IntegerField(
        "Year of examination",
        validators=[DataRequired(), NumberRange(min=1950, max=date.today().year + 1)],
    )
    college_name = StringField(
        "College name",
        filters=[strip_value],
        validators=[DataRequired(), Length(min=2, max=150)],
    )
    reason = TextAreaField(
        "Reason for requesting a duplicate",
        filters=[strip_value],
        validators=[DataRequired(), Length(min=10, max=1000)],
    )
    submit = SubmitField("Save application")


class StatusForm(FlaskForm):
    STATUSES = (
        "Not Started",
        "Documents Prepared",
        "Submitted",
        "Follow-up Required",
    )
    status = SelectField(
        "Status",
        choices=[(status, status) for status in STATUSES],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update status")
