# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from decimal import Decimal
from . import main
from .. import db
from ..decorators import user_has, user_is
from ..utils import gen_serial_no, Master, full_response, custom_response, R201_CREATED, R400_BADREQUEST, R200_OK
from app.models import Product, Order, OrderItem, OrderStatus, Warehouse, Store, ProductStock, ProductSku
from app.forms import OrderForm


def load_common_data():
    """
    私有方法，装载共用数据
    """
    pending_pay_count = Order.query.filter_by(master_uid=Master.master_uid(),status=OrderStatus.PENDING_PAYMENT).count()
    pending_review_count = Order.query.filter_by(master_uid=Master.master_uid(),status=OrderStatus.PENDING_CHECK).count()
    pending_ship_count = Order.query.filter_by(master_uid=Master.master_uid(),status=OrderStatus.PENDING_SHIPMENT).count()

    return {
        'pending_pay_count': pending_pay_count,
        'pending_review_count': pending_review_count,
        'pending_ship_count': pending_ship_count,
        'top_menu': 'orders'
    }

@main.route('/orders')
@main.route('/orders/<int:page>')
@user_has('admin_order')
def show_orders(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('s', 0, type=int)

    query = Order.query
    if status:
        query = query.filter_by(status=status)

    paginated_orders = query.order_by('created_at desc').paginate(page, per_page)

    return render_template('orders/show_list.html',
                           sub_menu='orders',
                           status=status,
                           paginated_orders=paginated_orders, **load_common_data())


@main.route('/orders/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_order')
def create_order():
    form = OrderForm()
    if request.method == 'POST':
        # 验证必须字段
        if not form.validate_on_submit():
            current_app.logger.debug(form.errors)
            return full_response(False, R400_BADREQUEST, form.errors)

        items = request.form.getlist('items[]')
        if not items or items is None:
            return custom_response(False, 'Order items is Null!')

        total_quantity = 0
        total_amount = 0
        total_discount = 0
        order_items = []
        for sku_id in items:
            sku_id = int(sku_id)
            quantity = request.form.get('quantity[%d]' % sku_id, type=int)
            discount = request.form.get('discount[%d]' % sku_id, type=float)

            # 验证sku信息
            product_sku = ProductSku.query.get(sku_id)
            if not product_sku:
                return custom_response(False, 'Product sku[%d] is not exist!' % sku_id)

            # 验证库存
            product_stock = ProductStock.query.filter_by(product_sku_id=sku_id, warehouse_id=form.warehouse_id.data).first()
            if product_stock.available_count < quantity:
                return custom_response(False, 'Inventory is not enough!')

            # 同步减去库存
            product_stock.current_count -= quantity
            product_stock.saled_count += quantity

            # 添加订单明细
            item = {
                'sku_id': sku_id,
                'sku_serial_no': product_sku.serial_no,
                'quantity': quantity,
                'deal_price': product_sku.sale_price, # 交易价格
                'discount_amount': Decimal(discount)  # 优惠金额
            }
            order_items.append(item)

            total_amount += product_sku.sale_price * quantity
            total_discount += discount
            total_quantity += quantity

        # 添加订单
        freight = form.freight.data
        pay_amount = Decimal(total_amount) + freight - Decimal(total_discount)
        new_serial_no = Order.make_unique_serial_no(form.serial_no.data)
        order = Order(
            master_uid=Master.master_uid(),
            serial_no=new_serial_no,
            outside_target_id=form.outside_target_id.data,
            store_id=form.store_id.data,
            warehouse_id=form.warehouse_id.data,
            pay_amount=Decimal(pay_amount),
            # 总金额
            total_amount=Decimal(total_amount),
            # 总数量
            total_quantity=total_quantity,
            discount_amount=Decimal(total_discount),
            freight=form.freight.data,
            express_id=0,
            remark=form.remark.data,
            buyer_name=form.buyer_name.data,
            buyer_tel=form.buyer_tel.data,
            buyer_phone=form.buyer_phone.data,
            buyer_zipcode=form.buyer_zipcode.data,
            buyer_address=form.buyer_address.data,
            buyer_country=form.buyer_country.data,
            buyer_province=form.buyer_province.data,
            buyer_city=form.buyer_city.data,
            # 买家备注
            buyer_remark=form.buyer_remark.data,
        )

        db.session.add(order)

        # 更新订单明细
        for item in order_items:
            item['order_serial_no'] = new_serial_no
            order_item = OrderItem(order=order, **item)
            db.session.add(order_item)

        db.session.commit()

        return full_response(True, R201_CREATED, {'next_url': url_for('.show_orders')})

    # 新增订单
    mode = 'create'
    # 获取店铺
    store_list = Store.query.filter_by(master_uid=Master.master_uid(), status=1).all()
    # 获取仓库列表
    warehouse_list = Warehouse.query.filter_by(master_uid=Master.master_uid(), status=1).all()
    # 添加默认订单号
    form.serial_no.data = gen_serial_no('C')

    return render_template('orders/create_and_edit.html',
                           form=form,
                           mode=mode,
                           store_list=store_list,
                           warehouse_list=warehouse_list, **load_common_data())


@main.route('/orders/<string:sn>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_order')
def edit_order(sn):
    pass


@main.route('/orders/<string:sn>/show')
@login_required
@user_has('admin_order')
def preview_order(sn):
    order = Order.query.filter_by(serial_no=sn).first()

    return render_template('orders/preview_order.html',
                           order_info=order, **load_common_data())


@main.route('/orders/ajax_verify', methods=['POST'])
@login_required
@user_has('admin_order')
def ajax_verify_order():
    selected_sns = request.form.getlist('selected[]')
    if not selected_sns or selected_sns is None:
        return custom_response(False, 'Verify order is NULL!')

    try:
        for sn in selected_sns:
            order = Order.query.filter_by(serial_no=sn).one()
            if order is None:
                return custom_response(False, "Verify order isn't exist!")

            if order.status == OrderStatus.PENDING_PAYMENT:
                # 等待审核
                order.mark_checked_status()
            elif order.status == OrderStatus.PENDING_CHECK:
                # 完成审核，待发货状态
                order.mark_shipment_status()
            else:
                pass

        db.session.commit()

    except:
        db.session.rollback()
        return custom_response(False, "Verify order is fail!!!")

    return full_response(True, R200_OK, selected_sns)