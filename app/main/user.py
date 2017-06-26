# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from app.models import User, Role, Ability
from app.forms import RoleForm, AbilityForm
import app.constant as constant
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, R500_BADREQUEST

@main.route('/users')
@main.route('/users/<int:page>')
@login_required
def show_users(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 0, type=int)

    if not status:
        query = User.query
    else:
        query = User.query.filter_by(status=status)

    paginated_users = query.order_by(User.created_at.desc()).paginate(page, per_page)

    return render_template('users/show_list.html',
                           paginated_users=paginated_users,
                           sub_menu='users',
                           department=constant.DEPARTMENT)


@main.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    pass

@main.route('/users/set_role/<int:user_id>', methods=['GET', 'POST'])
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

    roles = Role.query.all()
    return render_template('users/set_role.html',
                           roles=roles,
                           belong_roles=user.has_roles(),
                           post_url=url_for('.set_role', user_id=user_id))


@main.route('/roles')
@main.route('/roles/<int:page>')
def show_roles(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    form = RoleForm()

    paginated_roles = Role.query.order_by(Role.id.asc()).paginate(page, per_page)

    return render_template('users/show_roles.html',
                           paginated_roles=paginated_roles,
                           sub_menu='roles',
                           form=form)


@main.route('/roles/create', methods=['GET', 'POST'])
def create_role():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(
            name=form.name.data,
            title=form.title.data,
            description=form.description.data
        )
        db.session.add(role)
        db.session.commit()

        return full_response(True, R201_CREATED)

    return render_template('users/create_edit_role.html',
                           form=form,
                           post_url=url_for('.create_role')
                           )

@main.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
def edit_role(id):
    role = Role.query.get_or_404(id)
    form = RoleForm()
    if form.validate_on_submit():
        role.name = form.name.data
        role.title = form.title.data
        role.description = form.description.data

        db.session.commit()

        return full_response(True, R200_OK)

    # 填充数据
    form.name.data = role.name
    form.title.data = role.title
    form.description.data = role.description

    return render_template('users/create_edit_role.html',
                           form=form,
                           role=role,
                           post_url=url_for('.edit_role', id=id)
                           )

@main.route('/roles/delete', methods=['POST'])
def delete_role():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete role is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            role = Role.query.get_or_404(int(id))
            db.session.delete(role)
        db.session.commit()

        flash('Delete role is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete role is fail!', 'danger')

    return redirect(url_for('.show_roles'))


@main.route('/roles/set_ability/<int:role_id>', methods=['GET', 'POST'])
def set_ability(role_id):
    role = Role.query.get_or_404(role_id)
    if request.method == 'POST':
        selected_ids = request.form.getlist('selected[]')
        if not selected_ids or selected_ids is None:
            return full_response(False, custom_status('Ability id is NULL!!!'))

        abilities = []
        for aid in selected_ids:
            ability = Ability.query.get(int(aid))
            if ability is not None:
                abilities.append(ability)

        role.update_abilities(*abilities)

        flash('Set ability is ok.', 'success')
        return full_response(True, R201_CREATED)

    abilities = Ability.query.all()
    return render_template('users/set_ability.html',
                           abilities=abilities,
                           has_abilities=role.has_abilities(),
                           post_url=url_for('.set_ability', role_id=role_id))


@main.route('/abilities')
@main.route('/abilities/<int:page>')
def show_abilities(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_abilities = Ability.query.order_by(Ability.id.asc()).paginate(page, per_page)

    return render_template('users/show_abilities.html',
                           paginated_abilities=paginated_abilities,
                           sub_menu='abilities')


@main.route('/abilities/create', methods=['GET', 'POST'])
def create_ability():
    form = AbilityForm()
    if form.validate_on_submit():
        acl = Ability(
            name=form.name.data
        )
        db.session.add(acl)
        db.session.commit()

        flash('Add ability is success!', 'success')
        return redirect(url_for('.show_abilities'))

    return render_template('users/create_edit_ability.html',
                           form=form,
                           sub_menu='abilities')


@main.route('/abilities/<int:id>/edit', methods=['GET', 'POST'])
def edit_ability(id):
    ability = Ability.query.get_or_404(id)
    form = AbilityForm()
    if form.validate_on_submit():
        ability.name = form.name.data

        db.session.commit()

        flash('Edit ability is success!', 'success')
        return redirect(url_for('.show_abilities'))

    # 填充数据
    form.name.data = ability.name

    return render_template('users/create_edit_ability.html',
                           form=form,
                           sub_menu='abilities'
                           )

@main.route('/abilities/delete', methods=['POST'])
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