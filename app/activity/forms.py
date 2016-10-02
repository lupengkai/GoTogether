from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, DateTimeField, IntegerField,PasswordField

from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError
from flask.ext.pagedown.fields import PageDownField

from app.models import Role, User, Location
from datetime import datetime,timedelta



class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class EditActivityInfoForm(Form):
    start_time = DateTimeField('Starting Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    start_location = SelectField('Starting point', validators=[DataRequired()], coerce=int)
    end_location = SelectField('Destination', validators=[DataRequired(), ], coerce=int)

    max_people_amount = IntegerField('Max people amount', validators=[DataRequired(), ])
    contact_phone = StringField('Contact phone', validators=[DataRequired(),])
    description = PageDownField('description', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EditActivityInfoForm, self).__init__(*args, **kwargs)
        self.start_location.choices = [(location.id, location.name) for location in
                                       Location.query.order_by(Location.name).all()]
        self.end_location.choices = [(location.id, location.name) for location in
                                     Location.query.order_by(Location.name).all()]

    def validate_end_location(self, field):
        if field.data == self.start_location.data:
            raise ValidationError('Two place should be different!')

    def validate_start_time(self,field):
        if field.data < datetime.now():
            raise  ValidationError('You can not start before now')

    def validate_max_people_amount(self, field):
        if field.data < 2:
            raise ValidationError('The amount is at least 2!')