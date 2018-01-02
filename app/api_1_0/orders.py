# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Order, Address


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
    if order.user_id != g.current_user.id:
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
    pass


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

    # 数据验证
    products = request.get_json().get('products')
    address_rid = request.get_json().get('address_rid')
    if products is None:
        return custom_response('Order product is empty!', 403, False)
    if address_rid is None:
        return custom_response('Address param is empty!', 403, False)
    address = Address.query.filter_by(user_id=g.current_user.id, serial_no=address_rid).first()
    if address is None:
        return custom_response("Address isn't exist!", 403, False)
    
    try:
        append_dict = {
            'master_uid': g.master_uid,
            'serial_no': Order.make_unique_serial_no(),
            
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
        
        new_order = Order.create(order_data)
        
        db.session.add(new_order)
        db.session.commit()
    except:
        db.session.rollback()
        return custom_response('Create order failed!', 400, False)
    
    return full_response(R201_CREATED, new_order.to_json())


@api.route('/orders/delete', methods=['DELETE'])
@auth.login_required
def delete_order():
    """删除订单"""
    pass



