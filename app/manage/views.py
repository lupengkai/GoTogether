from flask import render_template, redirect, request, url_for, flash, abort
from flask.ext.admin import BaseView
from flask.ext.login import login_user, logout_user, login_required
from . import manage
from ..models import User,Admin,Permission, LocationApplication, Location
from .forms import LoginForm
from .. import db
from ..email import send_email
from flask.ext.login import current_user

from flask_admin.contrib import sqla
from flask_admin import helpers, expose

import flask_admin as admin

# Create customized model view class


# class ActivityModelView(sqla.ModelView):
#     def is_accessible(self):
#         print('is accessible' + str(current_user.is_authenticated))
#         print(current_user)
#         return current_user.is_authenticated and current_user.can(Permission.ORGANIZE_ACTIVITY)
#
#     def inaccessible_callback(self, name, **kwargs):
#         # redirect to login page if user doesn't have access
#         return redirect('/admin/login')
#     #admin.add_view(FileAdmin(path, '/static/', name='Static Files'))

# Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):#订制首页

    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not isinstance(current_user._get_current_object(), Admin):
            return redirect(url_for('.login_view'))
        return self.render('admin/index.html')

    @expose('/login', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if form.validate_on_submit():
            admin = Admin.query.filter_by(username=form.username.data).first()  # 调用init方法，再把数据库中的数据赋上
            if admin is not None and admin.password == form.password.data:
                    login_user(admin)  # whether remember
                    print('login')
                    print(current_user.is_authenticated)
                    return super(MyAdminIndexView, self).index()
                    # return self.index()

            flash('Invalid username or password.')

        return render_template('admin/login.html', form=form)



    @expose('/logout')
    def logout_view(self):
        logout_user()
        return redirect(url_for('admin.index'))




class MyModelView(sqla.ModelView): #info admin 的可见页面

    def is_accessible(self):
        # print('is accessible'+ str(current_user.is_authenticated))
        # print(current_user)
        return current_user.is_authenticated and current_user.can(Permission.ADMINISTER)

    def inaccessible_callback(self, name, **kwargs):
            # redirect to login page if user doesn't have access
        return redirect('/admin/login')

class InfoAdminView(BaseView): #info admin 的可见页面

    def is_accessible(self):
        # print('is accessible'+ str(current_user.is_authenticated))
        # print(current_user)
        return current_user.is_authenticated and current_user.can(Permission.ADMINISTER)

    def inaccessible_callback(self, name, **kwargs):
            # redirect to login page if user doesn't have access
        return redirect('/admin/login')
    @expose('/')
    def index(self):
        all_applications = LocationApplication.query.all()
        return self.render('admin/all_location_applications.html', all_applications=all_applications,Application=LocationApplication)

    @expose('/approve/<int:application_id>')
    def approve(self,application_id):
        application =  LocationApplication.query.get_or_404(application_id)
        if  Location.query.filter_by(name=application.name).first():
            flash('Location already exists!')
            return redirect(url_for('.index'))
        location = Location(name = application.name)
        db.session.add(location)
        return redirect(url_for('.index'))

