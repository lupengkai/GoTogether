from flask_admin import BaseView, expose
from flask import render_template, redirect, request, url_for, flash, abort
from flask.ext.login import login_user, logout_user, login_required
from . import activity
from ..models import User,Admin,Permission
from .forms import LoginForm
from .. import db
from ..email import send_email
from flask.ext.login import current_user
from datetime import datetime,timedelta
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from ..models import Activity,Location
import flask_admin as admin
from .forms import EditActivityInfoForm
class ActivityManageView(BaseView):
    def is_accessible(self):
        # print('is accessible' + str(current_user.is_authenticated))
        # print(current_user)
        return current_user.is_authenticated and current_user.can(Permission.ORGANIZE_ACTIVITY)

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/admin/login')

    @expose('/')
    def index(self):
        activities = Activity.query.all()
        return self.render('activity/index.html', activities=activities)
    @expose('/organize-activity',methods=['GET','POST'])
    def organize_activity(self):
        form = EditActivityInfoForm()
        if form.validate_on_submit():
            activity = Activity(start_time=(form.start_time.data - timedelta(hours=8)),
                          start_location=Location.query.get(form.start_location.data),
                          end_location=Location.query.get(form.end_location.data),
                          max_people_amount=form.max_people_amount.data,
                          description=form.description.data,
                             contact_phone=form.contact_phone.data
                          )



            db.session.add(activity)
            db.session.commit()
            flash('The activity has been delivered!')
            return self.activity(activity.id)
        return self.render('activity/organize_activity.html', form=form)

    @expose('/activity/<int:id>')
    def activity(self,id):
        activity = Activity.query.get_or_404(id)
        return self.render('activity/activity.html', activity=activity)

