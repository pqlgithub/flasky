# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Order, OrderItem, Address, ProductSku, Warehouse


@api.route('/orders')
@auth.login_required
def get_orders():
    """订单列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    status = request.values.get('status', type=int)
    prev = None
    next = None

    builder = Order.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id)
    
    if status:
        builder = builder.filter_by(status=status)
    
    pagination = builder.order_by(Order.created_at.desc()).paginate(page, per_page, error_out=False)

    orders = pagination.items
    if pagination.has_prev:
        prev = url_for('api.get_orders', status=status, page=page - 1, _external=True)

    if pagination.has_next:
        next = url_for('api.get_orders', status=status, page=page + 1, _external=True)
    
    return full_response(R200_OK, {
        'orders': [order.to_json() for order in orders],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/orders/<string:rid>')
@auth.login_required
def get_order(rid):
    """订单详情"""
    order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    if not is_owner(order.user_id):
        abort(401)
    
    return full_response(R200_OK, order.to_json())


@api.route('/orders/nowpay', methods=['POST'])
@auth.login_required
def nowpay():
    """支付接口"""
    pass


@api.route('/orders/freight')
@auth.login_required
def get_freight():
    """获取邮费"""
    freight = 0
    
    return full_response(R200_OK, {
        'freight': freight
    })


@api.route('/orders/<string:rid>/seller_remark', methods=['PUT'])
@auth.login_required
def add_seller_remark(rid):
    """添加卖家备注"""
    remark = request.json.get('remark')
    order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    if not can_admin(order.master_uid):
        abort(401)

    order.remark = remark

    db.session.commit()
    
    return status_response(R200_OK)
    

@api.route('/orders/<string:rid>/mark_delivery', methods=['POST'])
@auth.login_required
def mark_delivery(rid):
    """确认收货"""
    pass


@api.route('/orders/<string:rid>/track_logistic')
@auth.login_required
def track_logistic(rid):
    """物流跟踪查询接口"""
    pass


@api.route('/orders/print', methods=['POST'])
@auth.login_required
def print_order():
    """打印订单"""
    pass


@api.route('/orders/create', methods=['POST'])
@auth.login_required
def create_order():
    """新增订单"""
    
    # 验证订单商品
    # {"rid":"","quantity":1,"deal_price":23, "discount_amount":0, "warehouse_id": 0}
    products = request.get_json().get('items')
    if products is None:
        return custom_response('Order product is empty!', 403, False)
    
    # 验证收货地址
    address_rid = request.get_json().get('address_rid')
    if address_rid is None:
        return custom_response('Address param is empty!', 403, False)
    address = Address.query.filter_by(user_id=g.current_user.id, serial_no=address_rid).first()
    if address is None:
        return custom_response("Address isn't exist!", 403, False)

    # "{"address_rid":"5758463019",
    # "freight":0,
    # "invoice_type":1,
    # "buyer_remark":"包装需要好一些",
    # "from_client":2,
    # "affiliate_code":"",
    # "items":[
    # {"rid":"117280969019","quantity":1,"discount_amount":0},
    # {"rid":"118040911719","quantity":1,"discount_amount":0}
    # ]
    # }"
    
    try:
        total_quantity = 0
        total_amount = 0
        total_discount = 0
        order_items = []
        for product in products:
            rid = product['rid']
            # 验证sku信息
            product_sku = ProductSku.query.filter_by(serial_no=rid).first()
            if not product_sku:
                return custom_response("Product sku[%s] is not exist!" % rid, 403, False)
            # 验证库存
            warehouse_id = product.get('warehouse_id')
            quantity = product.get('quantity')
            
            if not warehouse_id: # 未选择库房，则默认库房
                default_warehouse = Warehouse.find_default_warehouse(g.master_uid)
                if default_warehouse is None:
                    return custom_response("Default Warehouse isn't setting!", 403, False)
                warehouse_id = default_warehouse.id
            
            product_stock = product_sku.stocks.filter_by(warehouse_id=warehouse_id).first()
            if not product_stock or product_stock.available_count < quantity:
                return custom_response("[%s] Inventory isn't enough!" % rid, 403, False)
            
            deal_price = float(product.get('deal_price'))
            discount_amount = Decimal(product.get('discount_amount'))
            
            order_items.append({
                'master_uid': g.master_uid,
                'warehouse_id': warehouse_id,
                'sku_id': product_sku.id,
                'sku_serial_no': rid,
                'quantity': quantity,
                'deal_price': deal_price,
                'discount_amount': discount_amount
            })
            
            total_quantity += quantity
            total_amount += deal_price * quantity
            total_discount += discount_amount

        outside_target_id = request.json.get('outside_target_id')
        freight = request.json.get('freight')
        pay_amount = Decimal(total_amount) + freight - Decimal(total_discount)
        order_serial_no = Order.make_unique_serial_no()
        append_dict = {
            'master_uid': g.master_uid,
            'user_id': g.current_user.id,
            'store_id': g.store_id,
            'serial_no': order_serial_no,
            'pay_amount': pay_amount,
            'total_amount': total_amount,
            'total_quantity': total_quantity,
            'discount_amount': total_discount,
            'outside_target_id': outside_target_id,
            
            'address_id': address.id,
            'buyer_name': address.full_name,
            'buyer_tel': address.phone,
            'buyer_phone': address.mobile,
            'buyer_zipcode': address.zipcode,
            'buyer_address': address.street_address,
            'buyer_country': address.country.name,
            'buyer_province': address.province,
            'buyer_city': address.city,
            'buyer_town': address.town,
            'buyer_area': address.city
        }
        order_data = dict(request.get_json(), **append_dict)
        current_app.logger.warn(order_data)
        
        # 添加订单
        new_order = Order.create(order_data)
        db.session.add(new_order)
        
        # 保存订单明细
        for item in order_items:
            item['order_serial_no'] = order_serial_no
            order_item = OrderItem(order=new_order, **item)
            
            db.session.add(order_item)
        
        db.session.commit()
    except Exception as err:
        current_app.logger.warn('Create order failed: %s' % str(err))
        db.session.rollback()
        return custom_response('Create order failed: %s' % str(err), 400, False)
    
    return full_response(R201_CREATED, new_order.to_json())


@api.route('/orders/cancel', methods=['POST'])
@auth.login_required
def cancel_order():
    """取消订单"""
    rid = request.json.get('rid')



@api.route('/orders/delete', methods=['DELETE'])
@auth.login_required
def delete_order():
    """删除订单"""
    rid = request.json.get('rid')



