# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from . import main
from .. import db
from ..utils import timestamp, gen_serial_no, full_response, status_response, custom_status, R200_OK
from ..constant import PURCHASE_STATUS, PURCHASE_PAYED
from app.models import PayAccount, TransactDetail, Invoice, Purchase, InWarehouse, InWarehouseProduct
from app.forms import PurchaseForm

top_menu = 'finances'


@main.route('/receives')
@main.route('/receives/<int:page>')
@login_required
def show_receives(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    type = request.args.get('t', 1, type=int)
    paginated_transactions = TransactDetail.query.filter_by(type=type).order_by('created_at asc').paginate(page, per_page)
    return render_template('finances/show_receives.html',
                           top_menu=top_menu,
                           sub_menu='receives',
                           type=type,
                           paginated_transactions=paginated_transactions)


@main.route('/payments')
@main.route('/payments/<int:page>')
@login_required
def show_payments(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('s', 1, type=int)
    paginated_payments = TransactDetail.query.filter_by(status=status, type=2).order_by('created_at asc').paginate(page,
                                                                                                           per_page, error_out=False)
    return render_template('finances/show_payments.html',
                           top_menu=top_menu,
                           sub_menu='payments',
                           status=status,
                           paginated_payments=paginated_payments)


@main.route('/payments/<int:id>/ajax_payed', methods=['POST'])
@login_required
def ajax_payed(id):
    """确认支付信息"""

    transaction = TransactDetail.query.get_or_404(int(id))
    # 更新支付状态
    transaction.status = 2
    transaction.payed_at = timestamp()

    # 支付完成，如果是采购单，更新采购单状态
    if transaction.target_type == 1:
        purchase = Purchase.query.get(transaction.target_id)
        purchase.update_status(5)
        purchase.update_payed(3)

        # 自动生成入库单
        in_warehouse = InWarehouse(
            master_uid=purchase.master_uid,
            serial_no=gen_serial_no('RK'),
            target_id=purchase.id,
            warehouse_id=purchase.warehouse_id,
            total_quantity=purchase.quantity_sum
        )
        db.session.add(in_warehouse)
        # 添加入库单明细
        items = []
        for product in purchase.products:
            item = {}
            item['product_sku_id'] = product.product_sku_id
            item['total_quantity'] = product.quantity

            new_item = InWarehouseProduct(in_warehouse=in_warehouse, **item)
            db.session.add(new_item)

    db.session.commit()

    return full_response(True, custom_status('Pay is finished!', 200), {'id': id})


@main.route('/payments/<int:id>/create', methods=['GET', 'POST'])
@login_required
def edit_payment(id):
    pass


@main.route('/transactions/create', methods=['GET', 'POST'])
@login_required
def create_transaction():

    return render_template('finances/create_and_edit.html')


@main.route('/transactions/<int:id>/create', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    pass




@main.route('/transactions/delete', methods=['POST'])
@login_required
def delete_transaction():
    pass


