from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, IntegerField, DateTimeField

from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError
from flask.ext.pagedown.fields import PageDownField

from app.models import Role, User, Location, LocationApplication
from datetime import datetime, timedelta


class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)])
    phone = StringField('Phone', validators=[DataRequired()])
    qq = StringField('QQ', validators=[DataRequired()])
    location = StringField('Location', validators=[Length(0, 64)])

    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditGroupInfoForm(Form):
    start_time = DateTimeField('Starting Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    start_location = SelectField('Starting point', validators=[DataRequired()], coerce=int)
    end_location = SelectField('Destination', validators=[DataRequired(), ], coerce=int)

    max_people_amount = IntegerField('Max people amount', validators=[DataRequired(), ])

    description = PageDownField('description', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EditGroupInfoForm, self).__init__(*args, **kwargs)
        self.start_location.choices = [(location.id, location.name) for location in
                                       Location.query.order_by(Location.name).all()]
        self.end_location.choices = [(location.id, location.name) for location in
                                     Location.query.order_by(Location.name).all()]

    def validate_end_location(self, field):
        if field.data == self.start_location.data:
            raise ValidationError('Two place should be different!')

    def validate_start_time(self, field):
        if field.data < datetime.now():
            raise ValidationError('You can not start before now')

    def validate_max_people_amount(self, field):
        if field.data < 2:
            raise ValidationError('The amount is at least 2!')


class ApplyLocationForm(Form):
    location_name = StringField('Location Name', validators=[DataRequired()])
    submit = SubmitField('Apply')

    def validate_location_name(self, field):
        if Location.query.filter_by(name=field.data).first():
            raise ValidationError('Location already exists')
        if LocationApplication.query.filter_by(name=field.data).first():
            raise ValidationError('The same location has been applied.Please wait.')
