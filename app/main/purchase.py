# -*- coding: utf-8 -*-
from jinja2 import PackageLoader, Environment
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_babelex import gettext
from io import BytesIO
import xhtml2pdf.pisa as pisa
import barcode
from barcode.writer import ImageWriter
from . import main
from .. import db
from ..utils import gen_serial_no, full_response, status_response, custom_status, R200_OK, Master
from ..constant import PURCHASE_STATUS, PURCHASE_PAYED
from ..decorators import user_has
from app.models import Purchase, PurchaseProduct, Supplier, Product, ProductSku, Warehouse, \
    TransactDetail, InWarehouse, StockHistory, ProductStock, Site
from app.forms import PurchaseForm, PurchaseExpressForm
from .filters import supress_none, timestamp2string, break_line


def load_common_data():
    """
    私有方法，装载共用数据
    """
    pending_review_count = Purchase.query.filter_by(master_uid=Master.master_uid(), status=1).count()
    pending_arrival_count = Purchase.query.filter_by(master_uid=Master.master_uid(), status=5).count()
    pending_storage_count = Purchase.query.filter_by(master_uid=Master.master_uid(), status=10).count()
    unpaid_count = Purchase.query.filter_by(master_uid=Master.master_uid(), payed=2).count()
    applyable_count = Purchase.query.filter_by(master_uid=Master.master_uid(), payed=1).count()

    return {
        'pending_review_count': pending_review_count,
        'pending_arrival_count': pending_arrival_count,
        'pending_storage_count': pending_storage_count,
        'applyable_count': applyable_count,
        'unpaid_count': unpaid_count,
        'top_menu': 'purchases'
    }


@main.route('/purchases')
@main.route('/purchases/<int:page>')
@login_required
@user_has('admin_purchase')
def show_purchases(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('s', 0, type=int)
    query = Purchase.query.filter_by(master_uid=Master.master_uid())
    if status:
        query = query.filter_by(status=status)

    paginated_purchases = query.order_by('created_at desc').paginate(page, per_page)

    return render_template('purchases/show_list.html',
                            paginated_purchases=paginated_purchases,
                            sub_menu='purchases',
                            purchase_status=PURCHASE_STATUS,
                            purchase_payed=PURCHASE_PAYED,
                            status=status,
                            **load_common_data())


@main.route('/purchases/payments')
@main.route('/purchases/payments/<int:page>')
@login_required
@user_has('admin_purchase')
def payments(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('f', 1, type=int)

    query = Purchase.query.filter_by(master_uid=Master.master_uid(), payed=status)

    paginated_purchases = query.order_by('created_at asc').paginate(page, per_page)

    return render_template('purchases/pay_list.html',
                           paginated_purchases=paginated_purchases,
                           sub_menu='purchases',
                           purchase_status=PURCHASE_STATUS,
                           purchase_payed=PURCHASE_PAYED,
                           f=status,
                           **load_common_data())

@main.route('/purchases/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_purchase')
def create_purchase():
    form = PurchaseForm()
    if form.validate_on_submit():
        # 获取选中的sku
        sku_list = request.form.getlist('sku[]')
        if not sku_list or sku_list is None:
            flash('Purchase not choose the products!', 'danger')
            return redirect(url_for('.show_purchases'))

        total_quantity = 0
        total_amount = 0
        purchase_products = []
        for sku_id in sku_list:
            sku = {}
            sku_id = int(sku_id)
            sku_row = ProductSku.query.get_or_404(sku_id)

            sku['product_sku_id'] = sku_id
            sku['sku_serial_no'] = sku_row.serial_no
            sku['cost_price'] = float(sku_row.cost_price)
            sku['quantity'] = int(request.form.get('sku[%d][quantity]' % sku_id))

            total_quantity += sku['quantity']
            total_amount += sku['cost_price'] * sku['quantity']

            purchase_products.append(sku)

        purchase = Purchase(
            master_uid=current_user.id,
            serial_no=Purchase.make_unique_serial_no(gen_serial_no('CG')),
            warehouse_id=form.warehouse_id.data,
            supplier_id=form.supplier_id.data,
            freight=form.freight.data,
            extra_charge=form.extra_charge.data,
            arrival_date=form.arrival_date.data,
            description=form.description.data,
            sku_count=len(sku_list),
            total_amount=total_amount,
            quantity_sum=total_quantity
        )
        db.session.add(purchase)

        for purchase_item in purchase_products:
            purchase_item = PurchaseProduct(purchase=purchase, **purchase_item)
            db.session.add(purchase_item)

        db.session.commit()

        flash('Add purchase is success!', 'success')
        return redirect(url_for('.show_purchases'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'create'
    suppliers = Supplier.query.order_by('created_at desc').all()
    warehouses = Warehouse.query.all()
    return render_template('purchases/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='purchases',
                           purchase=None,
                           suppliers=suppliers,
                           warehouses=warehouses,
                           purchase_status=PURCHASE_STATUS,
                           purchase_payed=PURCHASE_PAYED,
                           **load_common_data())


@main.route('/purchases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_purchase')
def edit_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    current_app.logger.debug(request.form)
    current_app.logger.debug(request.form.getlist('sku[]'))
    form = PurchaseForm()
    if form.validate_on_submit():
        # 获取选中的sku
        sku_list = request.form.getlist('sku[]')
        if not sku_list or sku_list is None:
            flash('Purchase not choose the products!', 'danger')
            return redirect(url_for('.show_purchases'))

        # 清空旧产品
        for old_item in purchase.products:
            db.session.delete(old_item)

        total_quantity = 0
        total_amount = 0
        for sku_id in sku_list:
            sku = {}
            sku_id = int(sku_id)
            sku_row = ProductSku.query.get_or_404(sku_id)

            sku['product_sku_id'] = sku_id
            sku['sku_serial_no'] = sku_row.serial_no
            sku['cost_price'] = float(sku_row.cost_price)
            sku['quantity'] = int(request.form.get('sku[%d][quantity]' % sku_id))

            total_quantity += sku['quantity']
            total_amount += sku['cost_price']*sku['quantity']

            # 添加新产品
            purchase_item = PurchaseProduct(purchase=purchase, **sku)
            db.session.add(purchase_item)

        purchase.warehouse_id = form.warehouse_id.data,
        purchase.supplier_id = form.supplier_id.data,
        purchase.freight = form.freight.data,
        purchase.extra_charge = form.extra_charge.data,
        purchase.arrival_date = form.arrival_date.data,
        purchase.description = form.description.data
        purchase.quantity_sum = total_quantity
        purchase.total_amount = total_amount
        purchase.sku_count = len(sku_list)

        db.session.commit()

        flash('Edit purchase is success!', 'success')
        return redirect(url_for('.show_purchases'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'edit'
    suppliers = Supplier.query.order_by('created_at desc').all()
    warehouses = Warehouse.query.all()

    form.warehouse_id.data = purchase.warehouse_id
    form.supplier_id.data = purchase.supplier_id
    form.freight.data = purchase.freight
    form.extra_charge.data = purchase.extra_charge
    form.arrival_date.data = purchase.arrival_date
    form.description.data = purchase.description

    return render_template('purchases/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='purchases',
                           purchase=purchase,
                           suppliers=suppliers,
                           warehouses=warehouses,
                           purchase_status=PURCHASE_STATUS,
                           purchase_payed=PURCHASE_PAYED,
                           **load_common_data())


@main.route('/purchases/delete', methods=['POST'])
@login_required
@user_has('admin_purchase')
def delete_purchase():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete purchase is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            purchase = Purchase.query.get_or_404(int(id))
            db.session.delete(purchase)
        db.session.commit()

        flash('Delete purchase is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete purchase is fail!', 'danger')

    return redirect(url_for('.show_purchases'))


@main.route('/purchases/delete_item', methods=['POST'])
@login_required
@user_has('admin_purchase')
def delete_purchase_item():
    item_id = request.form.get('item_id')
    purchase_item = PurchaseProduct.query.get(int(item_id))
    if not purchase_item:
        return custom_status('Purchase item is not exist!')

    sku_id = purchase_item.product_sku_id
    purchase_id = purchase_item.purchase_id
    purchase = Purchase.query.get(purchase_id)
    if not purchase:
        return custom_status('Purchase is not exist!')

    # 更新采购单数量、总金额
    purchase.sku_count -= 1
    purchase.quantity_sum -= purchase_item.quantity
    purchase.total_amount -= purchase_item.quantity*purchase_item.cost_price

    db.session.delete(purchase_item)
    db.session.commit()

    return full_response(True, R200_OK, {'sku_id': sku_id})


@main.route('/purchases/ajax_verify', methods=['POST'])
@login_required
@user_has('admin_purchase')
def ajax_verify():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        return status_response(False, custom_status('Delete purchase id is NULL!'))

    try:
        for id in selected_ids:
            purchase = Purchase.query.get(int(id))
            if purchase is None:
                return status_response(False, custom_status('Delete purchase id[%s] is NULL!' % id))
            # 审批完毕，待到货状态
            purchase.update_status(5)

        db.session.commit()
    except:
        db.session.rollback()
        return status_response(False, custom_status('Delete purchase is fail!'))

    return full_response(True, R200_OK, selected_ids)


@main.route('/purchases/<int:id>/ajax_arrival', methods=['GET', 'POST'])
@login_required
@user_has('admin_purchase')
def ajax_arrival(id):
    purchase = Purchase.query.get(id)
    if request.method == 'POST':
        quantity_offset = 0
        detail_products = []
        remark = request.form.get('remark')
        items = request.form.getlist('items[]')
        for sku_id in items:
            quantity = request.form.get('quantity[%s]' % sku_id, 0, type=int)
            if not quantity:
                continue

            item_product = purchase.products.filter_by(product_sku_id=sku_id).first()
            if not item_product.validate_quantity(quantity):
                return status_response(False, custom_status('Quantity exceeded total quantity!'))

            # 更新入库数量
            item_product.in_quantity += quantity
            # 新增总数量
            quantity_offset += quantity

            # 入库单明细
            ori_stock = ProductStock.get_stock_quantity(purchase.warehouse_id, sku_id)
            stock_history = StockHistory(
                master_uid=current_user.id,
                warehouse_id=purchase.warehouse_id,
                product_sku_id=sku_id,
                sku_serial_no=item_product.sku_serial_no,
                type=1,
                operation_type=10,
                original_quantity=ori_stock,
                quantity=quantity,
                current_quantity=ori_stock+quantity,
                ori_price=item_product.cost_price,
                price=item_product.cost_price,
            )
            detail_products.append(stock_history)

            # 更新库房累计库存数
            product_stock = ProductStock.validate_is_exist(purchase.warehouse_id, sku_id)
            if not product_stock:
                new_stock = ProductStock(
                    master_uid=Master.master_uid(),
                    product_sku_id=sku_id,
                    sku_serial_no=item_product.sku_serial_no,
                    warehouse_id=purchase.warehouse_id,
                    total_count=quantity,
                    current_count=quantity
                )
                db.session.add(new_stock)
            else:
                product_stock.total_count += quantity
                product_stock.current_count += quantity

        # 自动生成入库单
        in_serial_no = gen_serial_no('RK')
        in_warehouse = InWarehouse(
            master_uid=purchase.master_uid,
            serial_no=in_serial_no,
            target_serial_no=purchase.serial_no,
            warehouse_id=purchase.warehouse_id,
            total_quantity=quantity_offset,
            remark=remark
        )
        db.session.add(in_warehouse)
        # 添加操作明细
        for sh in detail_products:
            sh.serial_no = in_serial_no
            db.session.add(sh)

        # 检测是否完成入库
        if purchase.validate_finished(quantity_offset):
            # 入库完成
            purchase.update_status(15)
        purchase.in_quantity += quantity_offset

        db.session.commit()

        return status_response(True, R200_OK)

    return render_template('purchases/_modal_arrival.html',
                           purchase=purchase,
                           post_url=url_for('.ajax_arrival', id=id))


@main.route('/purchases/ajax_apply_pay', methods=['POST'])
@login_required
@user_has('admin_purchase')
def ajax_apply_pay():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        return status_response(False, custom_status('Apply purchase pay, id is NULL!'))

    try:
        for id in selected_ids:
            purchase = Purchase.query.get(int(id))
            if purchase is None:
                return status_response(False, custom_status('Apply purchase pay, id[%s] is NULL!' % id))
            if purchase.payed != 1:
                return status_response(False, custom_status('Purchase[%s] is already payed!' % id))

            # 申请付款，进入待付款流程
            purchase.update_payed(2)

            # 自动同步产生待付款单
            transaction = TransactDetail(
                master_uid=current_user.id,
                serial_no=gen_serial_no('FK'),
                type=2,
                transact_user=purchase.supplier.name,
                amount=purchase.total_amount,
                target_id=purchase.id,
                target_type=1
            )
            db.session.add(transaction)

        db.session.commit()
    except:
        db.session.rollback()
        return status_response(False, custom_status('Apply purchase is fail!'))

    return full_response(True, R200_OK, selected_ids)


@main.route('/purchases/<int:id>/add_express_no', methods=['GET', 'POST'])
@login_required
@user_has('admin_purchase')
def purchase_express_no(id):
    purchase = Purchase.query.get(id)
    form = PurchaseExpressForm()
    if form.validate_on_submit():
        purchase.express_name = form.express_name.data
        purchase.express_no = form.express_no.data

        db.session.commit()

        return status_response(True, R200_OK)

    form.express_name.data = purchase.express_name
    form.express_no.data = purchase.express_no
    return render_template('purchases/_modal_express.html',
                           purchase=purchase,
                           form=form,
                           post_url=url_for('.purchase_express_no', id=id))



@main.route('/purchases/output_purchase')
@login_required
@user_has('admin_purchase')
def output_purchase():
    rid = request.args.get('rid')
    rids = rid.split(',')
    purchase_list = Purchase.query.filter(Purchase.serial_no.in_(rids)).all()
    return render_template('pdf/purchase.html',
                           purchase_list=purchase_list)


@main.route('/purchases/print_purchase_pdf')
@login_required
@user_has('admin_purchase')
def print_purchase_pdf():
    """输出pdf，并打印"""
    rid = request.args.get('rid')
    rids = rid.split(',')
    purchase_list = Purchase.query.filter(Purchase.serial_no.in_(rids)).all()

    env = Environment(loader=PackageLoader(current_app.name, 'templates'))
    env.filters['supress_none'] = supress_none
    env.filters['timestamp2string'] = timestamp2string
    env.filters['break_line'] = break_line
    template = env.get_template('pdf/purchase.html')

    current_site = Site.query.filter_by(master_uid=Master.master_uid()).first()

    title_attrs = {
        'serial_no': gettext('Purchase Serial'),
        'status': gettext('Status'),
        'supplier' : gettext('Supplier'),
        'supplier_info': gettext('Supplier Info'),
        'warehouse_name' : gettext('Warehouse Name'),
        'date' : gettext('Date'),
        'contact_name' : gettext('Contact name'),
        'address': gettext('Address'),
        'phone': gettext('Phone'),
        'email': gettext('E-mail'),
        'remark': gettext('Remark'),
        'sn': gettext('Serial Number'),
        'product_info': gettext('Product Info'),
        'price': gettext('Price'),
        'quantity': gettext('Purchase Quantity'),
        'in_quantity': gettext('Arrival Quantity'),
        'subtotal': gettext('Subtotal'),
        'express_no': gettext('Express No.'),
        'freight': gettext('Freight'),
        'other_charge': gettext('Other Charge'),
        'total_amount': gettext('Total Amount')
    }

    code_bars = {}
    options = dict(text_distance=2,font_size=16)
    root_path = current_app.root_path + '/static/code_bars/'
    for sn in rids:
        ean = barcode.get('code39', sn, writer=ImageWriter())
        filename = 'serial_no_' + sn
        code_bars[sn] = ean.save(root_path + filename, options)
    
    html = template.render(
        current_site=current_site,
        title_attrs=title_attrs,
        code_bars=code_bars,
        font_path=current_app.root_path + '/static/fonts/simsun.ttf',
        purchase_list=purchase_list,
    ).encode('utf-8')

    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html), result)
    resp = make_response(result.getvalue())
    resp.headers['Content-Disposition'] = ("inline; filename='{0}'; filename*=UTF-8''{0}".format('test.pdf'))
    resp.headers['Content-Type'] = 'application/pdf'

    return resp

