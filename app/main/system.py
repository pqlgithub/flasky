# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from . import main
from .. import db
from app.models import User, Role, Ability, Site
from app.forms import RoleForm, AbilityForm, SiteForm, UserForm
import app.constant as constant
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, Master, custom_response


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'system'
    }

@main.route('/system/users')
@main.route('/system/users/<int:page>')
@login_required
def show_users(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 0, type=int)

    if not status:
        query = User.query
    else:
        query = User.query.filter_by(status=status)

    paginated_users = query.order_by(User.created_at.desc()).paginate(page, per_page)

    return render_template('system/show_list.html',
                           paginated_users=paginated_users,
                           sub_menu='users',
                           **load_common_data())


@main.route('/system/roles')
@main.route('/system/roles/<int:page>')
def show_roles(page=1):
    per_page = request.args.get('per_page', 10, type=int)

    paginated_roles = Role.query.order_by(Role.id.asc()).paginate(page, per_page)

    return render_template('system/show_roles.html',
                           paginated_roles=paginated_roles,
                           sub_menu='roles', **load_common_data())


@main.route('/system/abilities')
@main.route('/system/abilities/<int:page>')
def show_abilities(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_abilities = Ability.query.order_by(Ability.id.asc()).paginate(page, per_page)

    return render_template('system/show_abilities.html',
                           paginated_abilities=paginated_abilities,
                           sub_menu='abilities', **load_common_data())


@main.route('/system/abilities/create', methods=['GET', 'POST'])
def create_ability():
    form = AbilityForm()
    if form.validate_on_submit():
        acl = Ability(
            name=form.name.data,
            title=form.title.data
        )
        db.session.add(acl)
        db.session.commit()

        flash('Add ability is success!', 'success')
        return redirect(url_for('.show_abilities'))

    return render_template('system/create_edit_ability.html',
                           form=form,
                           sub_menu='abilities', **load_common_data())


@main.route('/system/abilities/<int:id>/edit', methods=['GET', 'POST'])
def edit_ability(id):
    ability = Ability.query.get_or_404(id)
    form = AbilityForm()
    if form.validate_on_submit():
        ability.name = form.name.data
        ability.title = form.title.data

        db.session.commit()

        flash('Edit ability is success!', 'success')
        return redirect(url_for('.show_abilities'))

    # 填充数据
    form.name.data = ability.name
    form.title.data = ability.title

    return render_template('system/create_edit_ability.html',
                           form=form,
                           sub_menu='abilities',
                            **load_common_data())


@main.route('/system/abilities/delete', methods=['POST'])
def delete_ability():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete ability is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            acl = Ability.query.get_or_404(int(id))
            db.session.delete(acl)
            db.session.commit()

        flash('Delete ability is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete ability is fail!', 'danger')

    return redirect(url_for('.show_abilities'))

