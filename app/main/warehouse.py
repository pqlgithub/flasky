# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_babelex import gettext
from sqlalchemy.sql import func
from . import main
from .. import db
from ..models import Warehouse, WarehouseShelve, InWarehouse, OutWarehouse, StockHistory, ProductStock, ProductSku,\
    Purchase, PurchaseProduct
from ..forms import WarehouseForm
from ..utils import full_response, custom_status, status_response,custom_response, R201_CREATED, R204_NOCONTENT, Master,\
    gen_serial_no, timestamp
from ..constant import SORT_TYPE_CODE, WAREHOUSE_OPERATION_TYPE
from ..decorators import user_has, user_is


def load_common_data():
    """
    私有方法，装载共用数据
    """
    warehouse_list = Warehouse.query.filter_by(status=1).all()
    return {
        'top_menu': 'warehouses',
        'warehouse_list': warehouse_list
    }


@main.route('/stocks', methods=['GET', 'POST'])
@main.route('/stocks/<int:page>', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def show_stocks(page=1):
    """显示库存清单"""
    per_page = request.values.get('per_page', 10, type=int)
    wh_id = request.values.get('wh_id', 0, type=int)
    s_t = request.values.get('s_t', 'ad')
    q_k = request.values.get('q_k')

    sort_type = SORT_TYPE_CODE.get(s_t, 'created_at')
    builder = ProductStock.query.filter_by(master_uid=Master.master_uid())
    if wh_id:
        builder = builder.filter_by(warehouse_id=wh_id)
    if q_k:
        builder = builder.filter_by(sku_serial_no=q_k)

    sort_by = '%s desc' % sort_type

    paginated_stocks = builder.order_by(sort_by).paginate(page, per_page)

    # 当前库存总数
    total_quantity = builder.with_entities(func.sum(ProductStock.current_count)).one()

    # 库存总金额
    total_amount = builder.join(ProductSku, ProductStock.product_sku_id==ProductSku.id)\
        .with_entities(func.sum(ProductStock.current_count*ProductSku.cost_price)).one()

    if request.method == 'POST':
        return render_template('warehouses/stock_table.html',
                               paginated_stocks=paginated_stocks,
                               total_quantity=total_quantity,
                               total_amount=total_amount,
                               wh_id=wh_id)

    return render_template('warehouses/show_stocks.html',
                           paginated_stocks=paginated_stocks,
                           total_quantity=total_quantity,
                           total_amount=total_amount,
                           sub_menu='stocks',
                           wh_id=wh_id, **load_common_data())


@main.route('/stocks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def edit_stock(id):
    pass


@main.route('/inout/<int:id>/preview')
@login_required
@user_has('admin_warehouse')
def preview_inout(id):
    """展示详情信息"""
    pass


@main.route('/inout')
@main.route('/inout/<int:page>')
@login_required
@user_has('admin_warehouse')
def show_inout(page=1):
    """显示库存变化明细"""
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('s', 0, type=int)
    paginated_inout_list = StockHistory.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(page, per_page)

    return render_template('warehouses/show_inout.html',
                           paginated_inout_list=paginated_inout_list,
                           sub_menu='inout',
                           status=status, **load_common_data())


@main.route('/ex_warehouse/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def create_ex_warehouse():
    """添加出库单"""
    if request.method == 'POST':
        warehouse_id = request.form.get('warehouse_id', type=int)
        operation_type = request.form.get('operation_type', type=int)
        items = request.form.getlist('items[]')
        if warehouse_id is None or operation_type is None:
            return custom_response(False, 'Warehouse or Type is Null!')
        if not items or items is None:
            return custom_response(False, 'Ex-warehouse has\'t products!')

        total_quantity = 0
        stock_items = []
        items = [int(sku_id) for sku_id in items]
        for sku_id in items:
            quantity = request.form.get('quantity[%d]' % sku_id, 0, type=int)
            if quantity == 0:
                continue
            warehouse_shelve_id = request.form.get('warehouse_shelve_id[%d]' % sku_id)

            item_product = ProductSku.query.get(sku_id)
            if not item_product:
                return custom_response(False, 'Sku is not found!')

            # 验证库存数量
            stock = ProductStock.query.filter_by(warehouse_id=warehouse_id, product_sku_id=sku_id).one()
            if stock.available_count < quantity:
                return custom_response(False, 'Inventory is not enough!')

            ori_quantity = stock.current_count
            # 更新库存数量
            stock.current_count -= quantity
            stock.manual_count += quantity

            # 添加出库记录明细
            stock_history = StockHistory(
                master_uid=Master.master_uid(),
                warehouse_id=warehouse_id,
                warehouse_shelve_id=warehouse_shelve_id,
                product_sku_id=sku_id,
                sku_serial_no=item_product.serial_no,
                type=2, # 出库
                operation_type=operation_type,
                original_quantity=ori_quantity,
                quantity=quantity,
                current_quantity=ori_quantity - quantity,
                ori_price=item_product.cost_price,
                price=item_product.cost_price
            )
            stock_items.append(stock_history)

            total_quantity += quantity

        # 添加手工出库单
        out_serial_no = gen_serial_no('CK')
        out_warehouse = OutWarehouse(
            master_uid=Master.master_uid(),
            serial_no=out_serial_no,
            target_serial_no=gen_serial_no('MG'),
            target_type=10,
            warehouse_id=warehouse_id,
            total_quantity=total_quantity,
            out_quantity=total_quantity,
            out_status=3
        )
        db.session.add(out_warehouse)

        # 添加操作明细
        for sh in stock_items:
            sh.serial_no = out_serial_no
            db.session.add(sh)

        db.session.commit()

        return status_response(True, R201_CREATED)

    # 获取仓库列表
    warehouse_list = Warehouse.query.filter_by(master_uid=Master.master_uid(), status=1).all()

    return render_template('warehouses/ex_warehouse_modal.html',
                           warehouses=warehouse_list)


@main.route('/inwarehouses', methods=['GET', 'POST'])
@main.route('/inwarehouses/<int:page>', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def show_in_warehouses(page=1):
    """显示入库单列表"""
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('s', 0, type=int)
    paginated_inwarehouses = InWarehouse.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(page, per_page)

    if request.method == 'POST':
        return render_template('warehouses/in_table.html',
                               paginated_inwarehouses=paginated_inwarehouses)

    return render_template('warehouses/show_inlist.html',
                           paginated_inwarehouses=paginated_inwarehouses,
                           sub_menu='inlist',
                           status=status, **load_common_data())


@main.route('/inwarehouses/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def create_in_warehouse():
    if request.method == 'POST':
        remark = request.form.get('remark')
        purchase_id = request.form.get('purchase_id', type=int)
        if purchase_id is None:
            return custom_response(False, 'No purchase is match!')

        current_purchase = Purchase.query.get(purchase_id)

        warehouse_id = request.form.get('warehouse_id', type=int)
        operation_type = request.form.get('operation_type', type=int)
        if warehouse_id is None or operation_type is None:
            return custom_response(False, 'Warehouse or Type is Null!')

        items = request.form.getlist('items[]')
        if not items or items is None:
            return custom_response(False, "In-warehouse has't products!")

        total_quantity = 0
        stock_items = []
        items = [int(sku_id) for sku_id in items]
        for sku_id in items:
            offset_quantity = request.form.get('quantity[%s]' % sku_id, 0, type=int)
            if offset_quantity == 0:
                continue # skip
            shelve_id = request.form.get('shelve[%s]' % sku_id, 0, type=int)
            if shelve_id == 0:
                continue # skip

            item_product = ProductSku.query.get(sku_id)
            if not item_product:
                return custom_response(False, 'Sku is not found!')

            # 更新采购明细
            purchase_product = PurchaseProduct.query.filter_by(purchase_id=purchase_id, product_sku_id=sku_id).first()
            if not purchase_product:
                return custom_response(False, 'Purchase product not match!')
            if purchase_product.quantity > purchase_product.in_quantity + offset_quantity:
                return custom_response(False, 'Quantity larger than purchase！')
            # 更新入库数量
            purchase_product.in_quantity += offset_quantity


            # 验证库存数量
            stock = ProductStock.query.filter_by(warehouse_id=warehouse_id, product_sku_id=sku_id).first()
            if not stock: # 添加
                new_stock = ProductStock(
                    master_uid = Master.master_uid(),
                    product_sku_id = sku_id,
                    sku_serial_no = item_product.serial_no,
                    warehouse_id = warehouse_id,
                    warehouse_shelve_id = shelve_id,
                    total_count = offset_quantity,
                    current_count = offset_quantity
                )
                db.session.add(new_stock)

                ori_quantity = 0
            else: # 更新库存
                ori_quantity = stock.current_count

                stock.total_count += offset_quantity
                stock.current_count += offset_quantity


            # 入库记录明细
            stock_history = StockHistory(
                master_uid=Master.master_uid(),
                warehouse_id=warehouse_id,
                warehouse_shelve_id=shelve_id,
                product_sku_id=sku_id,
                sku_serial_no=item_product.serial_no,
                type=1,  # 出库
                operation_type=operation_type,
                original_quantity=ori_quantity,
                quantity=offset_quantity,
                current_quantity=ori_quantity + offset_quantity,
                ori_price=item_product.cost_price,
                price=item_product.cost_price
            )
            stock_items.append(stock_history)

            total_quantity += offset_quantity

        # 更新采购单数量
        if current_purchase.in_quantity + total_quantity == current_purchase.quantity_sum:
            current_purchase.in_quantity += total_quantity
            # 完成入库
            current_purchase.update_status(15)
            current_purchase.arrival_at = timestamp()

        # 添加入库单
        in_serial_no = gen_serial_no('RK')
        in_warehouse = InWarehouse(
            master_uid = Master.master_uid(),
            serial_no = in_serial_no,
            target_serial_no = current_purchase.serial_no,
            target_type = 1,
            warehouse_id = warehouse_id,
            total_quantity = total_quantity,
            in_status = 1,
            status = 1,
            remark = remark
        )
        db.session.add(in_warehouse)

        # 保存入库明细
        for sh in stock_items:
            sh.serial_no = in_serial_no
            db.session.add(sh)

        db.session.commit()

        return status_response(True, R201_CREATED)
    # 获取仓库列表
    warehouse_list = Warehouse.query.filter_by(master_uid=Master.master_uid(), status=1).all()

    in_types = [type for type in WAREHOUSE_OPERATION_TYPE if type[0] in [10,13,16,19]]

    return render_template('warehouses/in_warehouse_modal.html',
                           warehouses=warehouse_list,
                           in_types=in_types)



@main.route('/inwarehouses/ajax_select_purchase', methods=['POST'])
@login_required
@user_has('admin_warehouse')
def ajax_select_purchase():
    """搜索待入库的采购单"""
    paginated_purchases = None
    wh_id = request.form.get('wh_id')
    page = request.values.get('page', 1, type=int)

    builder = Purchase.query.filter_by(master_uid=Master.master_uid()).filter(Purchase.status.in_((5,10)))

    if wh_id:
        builder = builder.filter_by(warehouse_id=wh_id)
        paginated_purchases = builder.order_by('created_at desc').paginate(page, 10)

    return render_template('warehouses/select_purchase_modal.html',
                           paginated_purchases=paginated_purchases,
                           wh_id=wh_id)

@main.route('/inwarehouse/ajax_submit_purchase', methods=['POST'])
@login_required
@user_has('admin_warehouse')
def ajax_submit_purchase():
    """获取选定的采购单明细"""
    selected_id = request.form.get('selected_id')
    if not selected_id:
        return "Missing request parameters"

    purchase = Purchase.query.get(int(selected_id))
    if purchase.master_uid != Master.master_uid():
        return "You haven't permission"

    # 获取仓库信息
    warehouse_id = purchase.warehouse_id
    warehouse= Warehouse.query.get(warehouse_id)

    return render_template('warehouses/purchase_item.html',
                           purchase=purchase,
                           warehouse=warehouse)


@main.route('/inwarehouses/<int:id>/preview')
@login_required
@user_has('admin_warehouse')
def preview_inwarehouse(id):
    pass


@main.route('/outwarehouses', methods=['GET', 'POST'])
@main.route('/outwarehouses/<int:page>', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def show_out_warehouses(page=1):
    """显示出库单列表"""
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('s', 0, type=int)
    paginated_outwarehouses = OutWarehouse.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(page, per_page)

    if request.method == 'POST':
        return render_template('warehouses/out_table.html',
                               paginated_outwarehouses=paginated_outwarehouses)

    return render_template('warehouses/show_outlist.html',
                           paginated_outwarehouses=paginated_outwarehouses,
                           sub_menu='outlist',
                           status=status, **load_common_data())


@main.route('/inwarehouses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def edit_in_warehouse(id):
    in_warehouse = InWarehouse.query.get_or_404(id)
    if request.method == 'POST':
        pass

    mode = 'edit'
    return render_template('warehouses/edit_in_warehouse.html',
                           sub_menu='inwarehouses',
                           mode=mode,
                           in_warehouse=in_warehouse, **load_common_data())


@main.route('/warehouses')
@main.route('/warehouses/<int:page>')
@login_required
@user_has('admin_warehouse')
def show_warehouses(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_warehouses = Warehouse.query.filter_by(master_uid=Master.master_uid()).order_by(Warehouse.id.asc()).paginate(page, per_page)
    return render_template('warehouses/show_list.html',
                           paginated_warehouses=paginated_warehouses,
                           sub_menu='warehouses', **load_common_data())


@main.route('/warehouses/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
def create_warehouse():
    form = WarehouseForm()
    if form.validate_on_submit():
        try:
            warehouse = Warehouse(
                master_uid=Master.master_uid(),
                name=form.name.data,
                address=form.address.data,
                en_address=form.en_address.data,
                description=form.description.data,
                username=form.username.data,
                phone=form.phone.data,
                email=form.email.data,
                qq=form.qq.data,
                type=int(form.type.data),
                is_default=bool(form.is_default.data),
                status=int(form.status.data)
            )
            db.session.add(warehouse)

            # 添加默认货架
            default_shelve = WarehouseShelve(
                warehouse=warehouse,
                name=gettext('Default Shelve'),
                type=1,
                description=gettext("default shelve, can't delete!"),
                is_default=True
            )
            db.session.add(default_shelve)

            db.session.commit()

            flash('Create warehouse is ok!', 'success')
        except Exception as ex:
            db.session.rollback()
            flash('Create warehouse is fail [%s]!' % ex, 'danger')

        return redirect(url_for('.show_warehouses'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'create'
    return render_template('warehouses/create_and_edit.html',
                           form=form,
                           mode=mode,
                           warehouse=None,
                           sub_menu='warehouses', **load_common_data())


@main.route('/warehouses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_warehouse')
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
                           mode=mode,
                           warehouse_id=id,
                           warehouse=warehouse,
                           sub_menu='warehouses', **load_common_data())


@main.route('/warehouses/delete', methods=['POST'])
@login_required
@user_has('admin_warehouse')
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
@user_has('admin_warehouse')
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
@login_required
@user_has('admin_warehouse')
def ajax_delete_shelve():
    shelve_id = request.form.get('id')
    if not shelve_id or shelve_id is None:
        return full_response(False, custom_status('Delete shelve id is null!'))

    shelve = WarehouseShelve.query.get(int(shelve_id))
    if shelve.is_default: # 默认货架
        return custom_response(False, "Default shelve can't delete!")

    db.session.delete(shelve)
    db.session.commit()

    return full_response(True, R204_NOCONTENT)
