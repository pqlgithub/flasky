# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from ..models import Warehouse, WarehouseShelve, InWarehouse
from ..forms import WarehouseForm
from ..utils import full_response, custom_status, R201_CREATED, R204_NOCONTENT

top_menu = 'warehouses'


@main.route('/inwarehouses')
@main.route('/inwarehouses/<int:page>')
@login_required
def show_in_warehouses(page=1):
    """显示入库单列表"""
    per_page = request.args.get('per_page', 10, type=int)
    paginated_inwarehouses = InWarehouse.query.order_by('created_at asc').paginate(page, per_page)

    return render_template('warehouses/show_inlist.html',
                           paginated_inwarehouses=paginated_inwarehouses,
                           top_menu=top_menu,
                           sub_menu='inwarehouses')





@main.route('/warehouses')
@main.route('/warehouses/<int:page>')
@login_required
def show_warehouses(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_warehouses = Warehouse.query.order_by(Warehouse.id.asc()).paginate(page, per_page)
    return render_template('warehouses/show_list.html',
                           paginated_warehouses=paginated_warehouses,
                           top_menu=top_menu,
                           sub_menu='warehouses'
                           )


@main.route('/warehouses/create', methods=['GET', 'POST'])
@login_required
def create_warehouse():
    form = WarehouseForm()
    if form.validate_on_submit():
        warehouse = Warehouse(
            user_id = current_user.id,
            name = form.name.data,
            address = form.address.data,
            en_address = form.en_address.data,
            description = form.description.data,
            username = form.username.data,
            phone = form.phone.data,
            email = form.email.data,
            qq = form.qq.data,
            type = int(form.type.data),
            is_default = bool(form.is_default.data),
            status = int(form.status.data)
        )
        db.session.add(warehouse)
        db.session.commit()

        try:
            flash('Create warehouse is ok!', 'success')
        except:
            db.session.rollback()
            flash('Create warehouse is fail!', 'danger')

        return redirect(url_for('.show_warehouses'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'create'
    return render_template('warehouses/create_and_edit.html',
                           form=form,
                           top_menu=top_menu,
                           mode=mode,
                           warehouse=None,
                           sub_menu='warehouses')


@main.route('/warehouses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_warehouse(id):
    warehouse = Warehouse.query.get_or_404(id)
    form = WarehouseForm()
    if form.validate_on_submit():
        form.populate_obj(warehouse)
        db.session.commit()

        flash('Edit warehouse is ok!', 'success')
        return redirect(url_for('.show_warehouses'))

    mode = 'edit'
    form.name.data = warehouse.name
    form.address.data = warehouse.address
    form.en_address.data = warehouse.en_address
    form.description.data = warehouse.description
    form.username.data = warehouse.username
    form.phone.data = warehouse.phone
    form.email.data = warehouse.email
    form.qq.data = warehouse.qq
    form.type.data = warehouse.type
    form.is_default.data = warehouse.is_default
    form.status.data = warehouse.status

    return render_template('warehouses/create_and_edit.html',
                           form=form,
                           top_menu=top_menu,
                           mode=mode,
                           warehouse_id=id,
                           warehouse=warehouse,
                           sub_menu='warehouses')

@main.route('/warehouses/delete', methods=['POST'])
@login_required
def delete_warehouse():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete warehouse is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            wh = Warehouse.query.get_or_404(int(id))
            db.session.delete(wh)
            db.session.commit()

        flash('Delete warehouse is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete warehouse is fail!', 'danger')

    return redirect(url_for('.show_warehouses'))


@main.route('/warehouses/add_shelve', methods=['POST'])
@login_required
def add_shelve():
    warehouse_id = request.form.get('warehouse_id')
    name = request.form.get('name')
    type = request.form.get('type')

    if name is None or name == '':
        return full_response(False, custom_status("Shelve name can't empty!"))

    if WarehouseShelve.query.filter_by(name=name).first():
        return full_response(False, custom_status("Shelve name already exist!"))

    shelve = WarehouseShelve(
        name = name,
        type = type,
        warehouse_id = warehouse_id
    )
    db.session.add(shelve)
    db.session.commit()

    return full_response(True, R201_CREATED, shelve.to_json())

@main.route('/warehouses/delete_shelve', methods=['POST'])
def ajax_delete_shelve():
    shelve_id = request.form.get('id')
    if not shelve_id or shelve_id is None:
        return full_response(False, custom_status('Delete shelve id is null!'))

    shelve = WarehouseShelve.query.get(int(shelve_id))
    db.session.delete(shelve)
    db.session.commit()

    return full_response(True, R204_NOCONTENT)
