from sqlalchemy import func
from flask import request, render_template, session, redirect, url_for, current_app, abort, flash, make_response
from flask.ext.login import login_required, current_user
from app.decorators import admin_required, permission_required
from . import main
from .forms import EditProfileForm, EditGroupInfoForm, ApplyLocationForm
from .. import db
from ..models import User, Role, Permission, Group, Location, Activity, LocationApplication
from ..email import send_email
from datetime import datetime, timedelta


@main.route('/', methods=['GET', 'POST'])
def index():
    print('index' + str(current_user))
    return render_template('base.html')


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('profile/user.html', user=user)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        current_user.phone = form.phone.data
        current_user.qq = form.qq.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.phone.data = current_user.phone
    form.qq.data = current_user.qq
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('profile/edit_profile.html', form=form)


@main.route('/establish-group', methods=['GET', 'POST'])  # 一旦发布便不能修改，无人情况下会自动删除
@login_required
def establish_group():
    form = EditGroupInfoForm()
    if form.validate_on_submit():
        group = Group(start_time=(form.start_time.data - timedelta(hours=8)),
                      start_location=Location.query.get(form.start_location.data),
                      end_location=Location.query.get(form.end_location.data),
                      max_people_amount=form.max_people_amount.data,
                      description=form.description.data
                      )
        group.build_user = current_user._get_current_object()
        group.users.append(group.build_user)

        db.session.add(group)
        db.session.commit()
        flash('The car sharing information has been delivered!')
        return redirect(url_for('main.group', id=group.id))

    return render_template('main/establish_group.html', form=form)


@main.route('/group/<int:id>', methods=['GET'])
def group(id):
    group = Group.query.get_or_404(id)
    if (datetime.now() > datetime.fromtimestamp(group.start_time)):
        flash('expired group!')
        return redirect(url_for('all_group'))
    return render_template('main/group.html', group=group)


@main.route('/activity/<int:id>', methods=['GET'])
def activity(id):
    activity = Activity.query.get_or_404(id)
    if (datetime.now() > datetime.fromtimestamp(activity.start_time)):
        flash('expired activity')
        return redirect(url_for('all_activity'))
    return render_template('main/activity.html', activity=activity)


@main.route('/join/<int:group_id>')
@login_required
def join(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user in group.users:
        flash('You are already in the group!')
    elif datetime.now() > datetime.fromtimestamp(group.start_time):
        flash('The group expires')
    elif group.users.count() == group.max_people_amount:
        flash('Sorry,we are full.')
    else:
        group.users.append(current_user._get_current_object())
        # db.session.add(group)
        # db.session.commit()
        flash('Join successfully')
    return redirect(url_for('main.group', id=group_id))


@main.route('/participate/<int:activity_id>')
@login_required
def participate(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if current_user in activity.users:
        flash('You are already in the activity!')
    elif datetime.now() > datetime.fromtimestamp(activity.start_time):
        flash('The activity expires')
    elif activity.users.count() == activity.max_people_amount:
        flash('Sorry,we are full.')
    else:
        activity.users.append(current_user._get_current_object())
        # db.session.add(group)
        # db.session.commit()
        flash('Join successfully')
    return redirect(url_for('main.activity', id=activity_id))


@main.route('/quit/<int:group_id>')
@login_required
def quit(group_id):
    group = Group.query.get_or_404(group_id)
    if not current_user in group.users:
        flash('You are not member of the group!')
    else:
        flash('Quit successfully!')
        group.users.remove(current_user._get_current_object())  # 涉及到数据库的用current_object
        # db.sesson.commit()
        if group.users.count() == 0:
            db.session.delete(group)
            return redirect(url_for('main.index'))
    return redirect(url_for('main.group', id=group_id))


@main.route('/leave/<int:activity_id>')
@login_required
def leave(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if not current_user in activity.users:
        flash('You are not member of the group!')
    else:
        flash('Quit successfully!')
        activity.users.remove(current_user._get_current_object())  # 涉及到数据库的用current_object
        # db.sesson.commit()

    return redirect(url_for('main.activity', id=activity_id))


@main.route('/group/all')
def all_group():
    alive_groups = Group.query.filter(Group.start_time > (datetime.now() - timedelta(hours=8))). \
        order_by(
        Group.start_time.desc()). \
        all()

    def is_not_full(group):
        return group.users.count() < group.max_people_amount

    # func.count((Group.users)) < Group.max_people_amount
    not_full_alive_group = list(filter(is_not_full, alive_groups))
    return render_template('main/all_group.html', groups=not_full_alive_group)


@main.route('/activity/all')
def all_activity():
    alive_activities = Activity.query.filter(Activity.start_time > (datetime.now() - timedelta(hours=8))). \
        order_by(
        Activity.start_time.desc()). \
        all()

    def is_not_full(activity):
        return activity.users.count() < activity.max_people_amount

    # func.count((Group.users)) < Group.max_people_amount
    not_full_alive_activities = list(filter(is_not_full, alive_activities))
    return render_template('main/all_group.html', activities=not_full_alive_activities)


@main.route('/my-ride')
@login_required
def my_ride():
    my_groups = current_user.groups_joinded
    my_activities = current_user.activities_joinded
    return render_template('main/my_ride.html', my_groups=my_groups, my_activities=my_activities)


@main.route('/apply-location', methods=['GET', 'POST'])
@login_required
def apply_location():
    form = ApplyLocationForm()
    if form.validate_on_submit():
        application = LocationApplication(name=form.location_name.data, user=current_user._get_current_object())
        db.session.add(application)
        db.session.commit()
        flash('Apply successfully!')
        return redirect(url_for('main.apply_location'))
    return render_template('main/apply_location.html', form=form)
