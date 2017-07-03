# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from app.models import Store, Asset, Site, User, Role, Ability
from app.forms import StoreForm, SiteForm, RoleForm
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, Master, custom_response
from ..decorators import user_has


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'settings'
    }


@main.route('/settings')
def show_settings():
    return redirect(url_for('.show_stores'))


@main.route('/site')
@login_required
@user_has('admin_setting')
def site():
    master_uid = Master.master_uid()
    site = Site.query.filter_by(master_uid=master_uid).first()

    return render_template('settings/site.html',
                           site=site,
                           sub_menu='sites')


@main.route('/site/setting', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def setting_site():
    mode = 'create',
    master_uid = Master.master_uid()
    site = Site.query.filter_by(master_uid=master_uid).first()
    form = SiteForm()
    if form.validate_on_submit():
        if site: # 更新信息
            form.populate_obj(site)
        else: # 新增信息
            site = Site(
                master_uid=Master.master_uid(),
                company_name=form.company_name.data,
                company_abbr=form.company_abbr.data,
                locale=form.locale.data,
                country=form.country.data,
                currency=form.currency.data,
                domain=form.domain.data,
                description=form.description.data
            )
            db.session.add(site)

        # 更新配置状态
        master = User.query.get_or_404(master_uid)
        master.mark_as_setting()

        db.session.commit()

        flash('Site info is ok!', 'success')
        return redirect(url_for('.site'))

    if site:
        mode = 'edit'
        # 初始编辑信息
        form.company_name.data = site.company_name
        form.company_abbr.data = site.company_abbr
        form.locale.data = site.locale
        form.country.data = site.country
        form.currency.data = site.currency
        form.domain.data = site.domain
        form.description.data = site.description

    return render_template('settings/setting_site.html',
                           mode=mode,
                           form=form,
                           sub_menu='sites',
                           **load_common_data())


@main.route('/stores')
@login_required
@user_has('admin_setting')
def show_stores():
    per_page = request.args.get('per_page', 20, type=int)
    paginated_stores = Store.query.order_by(Store.id.asc()).paginate(1, per_page)

    return render_template('stores/show_list.html',
                           sub_menu='stores',
                           paginated_stores=paginated_stores,
                           **load_common_data())


@main.route('/stores/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def create_store():
    form = StoreForm()
    if form.validate_on_submit():
        store = Store(
            name=form.name.data,
            platform=form.platform.data,
            master_uid=current_user.id
        )
        db.session.add(store)
        db.session.commit()

        flash('Add store is success!', 'success')
        return redirect(url_for('.show_stores'))

    return render_template('stores/create_and_edit.html',
                           form=form,
                           sub_menu='stores', **load_common_data())


@main.route('/stores/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def edit_store(id):
    store = Store.query.get_or_404(id)
    form = StoreForm()
    if form.validate_on_submit():
        store.name = form.name.data
        store.platform = form.platform.data

        db.session.commit()

        flash('Edit store is success!', 'success')
        return redirect(url_for('.show_stores'))

    # 填充数据
    form.name.data = store.name
    form.platform.data = store.platform

    return render_template('stores/create_and_edit.html',
                           form=form,
                           sub_menu='stores', **load_common_data())


@main.route('/stores/delete', methods=['POST'])
@login_required
@user_has('admin_setting')
def delete_store():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete store is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            store = Store.query.get_or_404(int(id))
            db.session.delete(store)
            db.session.commit()

        flash('Delete store is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete store is fail!', 'danger')

    return redirect(url_for('.show_stores'))



@main.route('/assets')
@main.route('/assets/<int:page>')
@login_required
@user_has('admin_setting')
def show_assets(page=1):
    per_page = request.args.get('per_page', 20, type=int)
    paginated_assets = Asset.query.order_by('created_at desc').paginate(page, per_page)

    return render_template('settings/show_assets.html',
                           sub_menu='assets',
                           paginated_assets=paginated_assets,
                           **load_common_data())


@main.route('/assets/delete', methods=['POST'])
@login_required
@user_has('admin_setting')
def delete_asset():
    pass


@main.route('/roles')
@main.route('/roles/<int:page>')
@login_required
@user_has('admin_setting')
def setting_roles(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    form = RoleForm()
    paginated_roles = Role.query.filter_by(master_uid=Master.master_uid()).paginate(page, per_page)

    return render_template('settings/show_roles.html',
                           paginated_roles=paginated_roles,
                           sub_menu='roles',
                           form=form)


@main.route('/roles/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def create_role():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(
            master_uid=Master.master_uid(),
            name=form.name.data,
            title=form.title.data,
            description=form.description.data
        )
        db.session.add(role)
        db.session.commit()

        return full_response(True, R201_CREATED)

    return render_template('settings/create_edit_role.html',
                           form=form,
                           post_url=url_for('.create_role')
                           )


@main.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
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

    return render_template('settings/create_edit_role.html',
                           form=form,
                           role=role,
                           post_url=url_for('.edit_role', id=id)
                           )

@main.route('/roles/delete', methods=['POST'])
@login_required
@user_has('admin_setting')
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
@login_required
@user_has('admin_setting')
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
    return render_template('settings/set_ability.html',
                           abilities=abilities,
                           has_abilities=role.has_abilities(),
                           post_url=url_for('.set_ability', role_id=role_id))