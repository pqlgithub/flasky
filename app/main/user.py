# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from app.models import User, Role, Ability, Site
from app.forms import RoleForm, AbilityForm, SiteForm, UserForm
import app.constant as constant
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, Master, custom_response
from ..decorators import user_has

def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'settings'
    }

@main.route('/users/profile', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def profile():
    return render_template('users/profile.html')


@main.route('/site/child_users')
@login_required
@user_has('admin_setting')
def child_users():
    master_uid = Master.master_uid()
    per_page = request.args.get('per_page', 50, type=int)

    paginated_users = User.query.filter_by(master_uid=master_uid).order_by('created_at desc').paginate(1, per_page)

    return render_template('users/child_users.html',
                           paginated_users=paginated_users,
                           sub_menu='child_users')


@main.route('/site/add_child_user', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def add_child_user():
    master_uid = Master.master_uid()
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            master_uid = master_uid,
            email = form.email.data,
            username = form.username.data,
            password = form.password.data,
            confirmed = True,
            is_setting = True,
            time_zone = 'zh')
        db.session.add(user)
        db.session.commit()

        return custom_response(True, 'Add user is ok!')

    site = Site.query.filter_by(master_uid=master_uid).first()
    return render_template('users/add_child_user.html',
                           form=form,
                           site=site)


@main.route('/users/set_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        selected_ids = request.form.getlist('selected[]')
        if not selected_ids or selected_ids is None:
            return full_response(False, custom_status('Role id is NULL!!!'))

        roles = []
        for rid in selected_ids:
            role = Role.query.get(int(rid))
            if role is not None:
                roles.append(role)

        user.update_roles(*roles)

        flash('Set role is ok.', 'success')
        return full_response(True, R201_CREATED)

    roles = Role.query.filter_by(master_uid=Master.master_uid()).all()
    return render_template('users/set_role.html',
                           roles=roles,
                           belong_roles=[r.name for r in user.roles],
                           post_url=url_for('.set_role', user_id=user_id))


@main.route('/users/passwd', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def passwd():
    """更新密码"""
    return render_template('users/passwd.html')