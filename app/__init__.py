from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.pagedown import PageDown

from config import config

from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_admin.contrib.fileadmin import FileAdmin
from flask.ext.admin.contrib import sqla
import os.path as op

from flask import request, render_template, session, redirect, url_for, current_app, abort, flash, make_response
from flask.ext.login import login_required, current_user

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'None'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    pagedown.init_app(app)

    from .manage.views import MyAdminIndexView
    admin = Admin(app, name='Go Together', index_view=MyAdminIndexView(), template_mode='bootstrap3')

    path = op.join(op.dirname(__file__), 'static')
    from app.models import User, Role, Group, Message, Location, Activity, Permission
    from app.models import Admin as ad
    from .manage.views import MyModelView,InfoAdminView
    from .activity.views import ActivityManageView

    admin.add_view(MyModelView(User, db.session))
    admin.add_view(MyModelView(Group, db.session))
    admin.add_view(MyModelView(Location, db.session))
    admin.add_view(MyModelView(Activity, db.session, endpoint='adtivities'))
    admin.add_view(MyModelView(ad, db.session, name='Administrator', endpoint='administrator'))
    # admin.add_view(InfoAdminView(name='Location Application', endpoint='location_application',category='Info Admin'))
    # admin.add_view(InfoAdminView(name='Other Message', endpoint='other_message',category='Info Admin'))

    admin.add_view(InfoAdminView(name='Location Application', endpoint='location_application'))

    admin.add_view(ActivityManageView(name='ActivityAdmin', endpoint='activity_admin'))


    login_manager.init_app(app)


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .activity import activity as activity_blueprint
    app.register_blueprint(activity_blueprint, url_prefix='/activity')

    from .manage import manage as manage_blueprint
    app.register_blueprint(manage_blueprint, url_prefix='/manage')

    return app
