from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    SubmitField,
    PasswordField,
)

from wtforms.validators import DataRequired


class PatientSearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Continue")


class LoginForm(FlaskForm):
    employee_code = StringField("Employee Code", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    employee_code = StringField("Employee Code", validators=[DataRequired()])
    full_name = StringField("Full Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")
