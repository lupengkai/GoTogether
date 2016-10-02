from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, DateTimeField, IntegerField, \
    PasswordField

from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError
from flask.ext.pagedown.fields import PageDownField

from app.models import Role, User, Location
from datetime import datetime, timedelta

class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
