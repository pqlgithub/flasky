# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from ..decorators import user_has, user_is
from ..utils import Master
from app.models import Express, Shipper, Warehouse
from app.forms import ExpressForm, EditExpressForm, ShipperForm


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'logistics'
    }

@main.route('/logistics')
@main.route('/logistics/<int:page>')
@user_has('admin_logistics')
def show_expresses(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_express = Express.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(page, per_page)

    return render_template('logistics/show_list.html',
                           sub_menu='express',
                           paginated_express=paginated_express,
                           **load_common_data())


@main.route('/expresses/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_logistics')
def create_express():
    form = ExpressForm()
    if form.validate_on_submit():
        express = Express(
            master_uid = Master.master_uid(),
            name = form.name.data,
            contact_name = form.contact_name.data,
            contact_mobile = form.contact_mobile.data,
            contact_phone = form.contact_phone.data,
            description = form.description.data
        )

        db.session.add(express)
        db.session.commit()

        flash('Add express id ok!', 'success')
        return redirect(url_for('.show_expresses'))

    return render_template('logistics/create_and_edit.html',
                           form=form,
                           sub_menu='express',
                           mode='create')


@main.route('/expresses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_logistics')
def edit_express(id):
    express = Express.query.get_or_404(id)
    form = EditExpressForm(express)
    if form.validate_on_submit():
        form.populate_obj(express)
        db.session.commit()

        flash('Edit express id ok!', 'success')
        return redirect(url_for('.show_expresses'))

    # 初始化编辑数据
    form.name.data = express.name
    form.contact_name.data = express.contact_name
    form.contact_mobile.data = express.contact_mobile
    form.contact_phone.data = express.contact_phone
    form.description.data = express.description

    return render_template('logistics/create_and_edit.html',
                           form=form,
                           sub_menu='express',
                           mode='create')


@main.route('/expresses/delete', methods=['POST'])
@login_required
@user_has('admin_logistics')
def delete_express():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete express is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            express = Express.query.get_or_404(int(id))
            db.session.delete(express)

        db.session.commit()

        flash('Delete express is ok!', 'success')
    except:
        db.session.rollback()

        flash('Delete express is fail!', 'danger')

    return redirect(url_for('.show_expresses'))


@main.route('/shippers')
@main.route('/shippers/<int:page>')
@login_required
@user_has('admin_logistics')
def show_shippers(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_shippers = Shipper.query.order_by('created_at desc').paginate(page, per_page)

    return render_template('logistics/show_shippers.html',
                           sub_menu='shipper',
                           paginated_shippers=paginated_shippers, **load_common_data())


@main.route('/shippers/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_logistics')
def create_shipper():
    form = ShipperForm()
    if form.validate_on_submit():
        shipper = Shipper(
            master_uid = Master.master_uid(),
            warehouse_id = form.warehouse_id.data,
            name = form.name.data,
            phone = form.phone.data,
            mobile = form.mobile.data,
            zipcode = form.zipcode.data,
            from_city = form.from_city.data,
            province = form.province.data,
            city = form.city.data,
            area = form.area.data,
            address = form.address.data
        )
        db.session.add(shipper)
        db.session.commit()

        flash('Add shipper id ok!', 'success')
        return redirect(url_for('.show_shippers'))

    # 获取仓库列表
    warehouse_list = Warehouse.query.filter_by(master_uid=Master.master_uid(), status=1).all()

    return render_template('logistics/create_edit_shipper.html',
                           form=form,
                           sub_menu='shipper',
                           mode='create',
                           warehouse_list=warehouse_list)


@main.route('/shippers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_logistics')
def edit_shipper(id):
    shipper = Shipper.query.get_or_404(id)
    form = ShipperForm()
    if form.validate_on_submit():
        form.populate_obj(shipper)
        db.session.commit()

        flash('Edit shipper id ok!', 'success')
        return redirect(url_for('.show_shippers'))

    # 初始化编辑数据
    form.warehouse_id.data = shipper.warehouse_id
    form.name.data = shipper.name
    form.phone.data = shipper.phone
    form.mobile.data = shipper.mobile
    form.zipcode.data = shipper.zipcode
    form.from_city.data = shipper.from_city
    form.province.data = shipper.province
    form.city.data = shipper.city
    form.area.data = shipper.area
    form.address.data = shipper.address

    # 获取仓库列表
    warehouse_list = Warehouse.query.filter_by(master_uid=Master.master_uid(), status=1).all()

    return render_template('logistics/create_edit_shipper.html',
                           form=form,
                           sub_menu='shipper',
                           mode='create',
                           warehouse_list=warehouse_list)



@main.route('/shippers/delete', methods=['POST'])
@login_required
@user_has('admin_logistics')
def delete_shipper():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete shipper is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            shipper = Shipper.query.get_or_404(int(id))
            db.session.delete(shipper)

        db.session.commit()

        flash('Delete shipper is ok!', 'success')
    except:
        db.session.rollback()

        flash('Delete shipper is fail!', 'danger')

    return redirect(url_for('.show_shippers'))