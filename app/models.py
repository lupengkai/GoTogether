from random import randint, seed

from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from datetime import datetime
import hashlib
from markdown import markdown
import bleach
from app.exceptions import ValidationError
import re


class Permission:
    JOIN_GROUP = 0X01
    JOIN_ACTIVITY = 0X02
    ESTABLISH_GROUP = 0X04
    ORGANIZE_ACTIVITY = 0X08
    ADMINISTER = 0X80


class Role(db.Model):  # 以后系统扩大　用户及管理员分的层级越多
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permission = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    admins = db.relationship('Admin', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': ((Permission.JOIN_GROUP | Permission.JOIN_ACTIVITY | Permission.ESTABLISH_GROUP), True),

            'ActivityAdmin': (Permission.ORGANIZE_ACTIVITY, False),

            'InfoAdmin': (Permission.ADMINISTER, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permission = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


join1 = db.Table('join1',
                 db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
                 db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
                 )

join2 = db.Table('join2',
                 db.Column('activity_id', db.Integer, db.ForeignKey('activities.id')),
                 db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
                 )


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    phone = db.Column(db.String(64), unique=True)
    qq = db.Column(db.String(64), unique=True)  # 暂时这样代替　以后可能联合登陆
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    name = db.Column(db.String(64))
    location = db.Column(db.String())
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    groups_joinded = db.relationship('Group', secondary=join1, backref=db.backref('users', lazy='dynamic'),
                                     lazy='dynamic')

    groups_builded = db.relationship('Group', backref='build_user', lazy='dynamic')

    activities_joinded = db.relationship('Activity', secondary=join2, backref=db.backref('users', lazy='dynamic'),
                                         lazy='dynamic')

    messages = db.relationship('Message', backref='user', lazy='dynamic')
    location_applications = db.relationship('LocationApplication', backref='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def reset_password(self, token, password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.password = password
        db.session.add(self)
        return True

    def can(self, permission):
        return self.role is not None and \
               (self.role.permission & permission) == permission

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://cdn.v2ex.com/gravatar'
        else:
            url = 'http://cdn.v2ex.com/gravatar/'
        hash = self.avatar_hash or hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating
        )

    def get_id(self):
        return 'User-' + str(self.id)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def __repr__(self):
        return '<User %r>' % self.username


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    description_html = db.Column(db.Text)
    start_time = db.Column(db.DateTime)

    max_people_amount = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    builder_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    start_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    end_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))

    start_location = db.relationship('Location', foreign_keys=[start_location_id])
    end_location = db.relationship('Location', foreign_keys=[end_location_id])

    @staticmethod
    def get_alive_group():
        # 查询有人的还没有到时间的人还没满的
        alive_groups = Group.query.filter(len(Group.users) < Group.max_people_amount).order_by(
            Group.start_time.desc()).all()

        return alive_groups

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']

        target.description_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


db.event.listen(Group.description, 'set', Group.on_changed_body)


class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def get_id(self):
        return 'Admin-' + str(self.id)

    def can(self, permission):
        return self.role is not None and \
               (self.role.permission & permission) == permission

    @property
    def is_authenticated(self):
        return True


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True)

    def __repr__(self):
        return '<Location %r>' % self.name


class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    description_html = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    contact_phone = db.Column(db.String(64))

    max_people_amount = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    start_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    end_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))

    start_location = db.relationship('Location', foreign_keys=[start_location_id])
    end_location = db.relationship('Location', foreign_keys=[end_location_id])


class LocationApplication(db.Model):
    __tablename__ = 'location_applications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


@login_manager.user_loader
def load_user(user_id):
    identifier = re.match(r'^(\w+)\-(\d+)$', user_id)
    # print(user_id)
    # aa = Admin.query.get(identifier.group(2))
    # print('load' + str(aa))
    # return exec(identifier.group(1)+'.query.get('+identifier.group(2)+')')
    if identifier.group(1) == 'User':
        return User.query.get(identifier.group(2))
    else:
        return Admin.query.get(identifier.group(2))
        # return User.query.get(user_id)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permission):
        return False


login_manager.anonymous_user = AnonymousUser
