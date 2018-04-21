# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user, logout_user
from flask_babelex import gettext
from . import main
from .. import db
from app.models import User, Role, UserIdType, Site, Store
from app.forms import RoleForm, AbilityForm, SiteForm, UserForm, PasswdForm, PreferenceForm, UserEditForm
from ..utils import full_response, custom_status, R201_CREATED, Master, custom_response, form_errors_list, \
    form_errors_response
from ..decorators import user_has


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'settings'
    }


@main.route('/users/profile', methods=['GET', 'POST'])
def profile():
    return render_template('users/profile.html')


@main.route('/users/preference', methods=['GET', 'POST'])
def preference():
    form = PreferenceForm()

    if form.validate_on_submit():
        current_user.locale = form.locale.data

        db.session.commit()

        flash(gettext('Update preference setting is ok!'), 'success')

        return redirect(url_for('main.index'))

    form.locale.data = current_user.locale

    return render_template('users/preference.html',
                           form=form)


@main.route('/site/child_users')
@user_has('admin_setting')
def child_users():
    master_uid = Master.master_uid()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    paginated_users = User.query.filter_by(master_uid=master_uid).order_by(User.created_at.desc())\
        .paginate(page, per_page)
    
    return render_template('users/child_users.html',
                           paginated_users=paginated_users,
                           sub_menu='child_users')


@main.route('/site/add_child_user', methods=['GET', 'POST'])
@user_has('admin_setting')
def add_child_user():
    master_uid = Master.master_uid()

    stores = Store.query.filter_by(master_uid=master_uid).all()

    form = UserForm()
    form.store_id.choices = [(store.id, store.name) for store in stores]
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User()

            user.master_uid = master_uid
            user.email = form.email.data
            user.username = form.username.data
            user.password = form.password.data

            user.store_id = form.store_id.data

            # 默认为供应商身份
            user.id_type = UserIdType.SUPPLIER
            user.confirmed = True
            user.is_setting = True
            user.time_zone = 'zh'

            db.session.add(user)

            db.session.commit()
        else:
            error_list = form_errors_list(form)
            return form_errors_response(error_list)

        return custom_response(True, 'Add user is ok!')

    mode = 'create'
    site = Site.query.filter_by(master_uid=master_uid).first()

    return render_template('users/add_child_user.html',
                           post_url=url_for('.add_child_user'),
                           mode=mode,
                           form=form,
                           site=site)


@main.route('/site/edit_user/<int:user_id>', methods=['GET', 'POST'])
@user_has('admin_setting')
def edit_user(user_id):
    """更新用户信息"""
    user = User.query.get_or_404(user_id)
    stores = Store.query.filter_by(master_uid=Master.master_uid()).all()

    form = UserEditForm()
    form.store_id.choices = [(store.id, store.name) for store in stores]
    if request.method == 'POST':
        current_app.logger.debug('User store_id: %d' % form.store_id.data)
        if form.validate_on_submit():
            # 验证用户名是否唯一
            if user.username != form.username.data and User.query.filter_by(username=form.username.data).first():
                return custom_response(False, '用户名[%s]已存在！' % form.username.data)

            user.username = form.username.data
            user.store_id = form.store_id.data

            db.session.commit()
        else:
            error_list = form_errors_list(form)
            return form_errors_response(error_list)

        return custom_response(True, 'Edit user is ok!')

    mode = 'edit'
    site = Site.query.filter_by(master_uid=Master.master_uid()).first()

    form.username.data = user.username
    form.store_id.data = user.store_id

    return render_template('users/add_child_user.html',
                           post_url=url_for('.edit_user', user_id=user_id),
                           mode=mode,
                           form=form,
                           user=user,
                           site=site)


@main.route('/users/set_role/<int:user_id>', methods=['GET', 'POST'])
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
@user_has('admin_setting')
def passwd():
    """更新密码"""
    form = PasswdForm()
    if form.validate_on_submit():
        current_user.password = form.password.data

        db.session.commit()
        # 强制退出
        logout_user()

        flash('Update password is ok!', 'success')

        return redirect(url_for('auth.login'))

    return render_template('users/passwd.html',
                           sub_menu='passwd',
                           form=form,
                           **load_common_data())
