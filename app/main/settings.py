# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from app.models import Store, Asset
from app.forms import StoreForm

top_menu = 'settings'
sub_menu = 'stores'

@main.route('/settings')
def show_settings():
    return redirect(url_for('.show_stores'))

@main.route('/stores')
def show_stores():
    per_page = request.args.get('per_page', 20, type=int)
    paginated_stores = Store.query.order_by(Store.id.asc()).paginate(1, per_page)

    return render_template('stores/show_list.html',
                           top_menu=top_menu,
                           sub_menu=sub_menu,
                           paginated_stores=paginated_stores,
                           )

@main.route('/stores/create', methods=['GET', 'POST'])
def create_store():
    form = StoreForm()
    if form.validate_on_submit():
        store = Store(
            name=form.name.data,
            platform=form.platform.data,
            user_id=current_user.id
        )
        db.session.add(store)
        db.session.commit()

        flash('Add store is success!', 'success')
        return redirect(url_for('.show_stores'))

    return render_template('stores/create_and_edit.html',
                           form=form,
                           top_menu=top_menu,
                           sub_menu=sub_menu)


@main.route('/stores/<int:id>/edit', methods=['GET', 'POST'])
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
                           top_menu=top_menu,
                           sub_menu=sub_menu
                           )

@main.route('/stores/delete', methods=['POST'])
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
def show_assets(page=1):
    per_page = request.args.get('per_page', 20, type=int)
    paginated_assets = Asset.query.order_by('created_at desc').paginate(page, per_page)

    return render_template('settings/show_assets.html',
                           top_menu=top_menu,
                           sub_menu='assets',
                           paginated_assets=paginated_assets,
                           )


@main.route('/assets/delete', methods=['POST'])
@login_required
def delete_asset():
    pass

