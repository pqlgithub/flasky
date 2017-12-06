# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Order


@api.route('/orders')
@auth.login_required
def get_orders():
    """订单列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    status = request.values.get('status', type=int)
    prev = None
    next = None

    builder = Order.query.filter_by(master_uid=g.master_uid)
    if status:
        builder = builder.filter_by(status=status)
    
    pagination = builder.order_by('created_at desc').paginate(page, per_page, error_out=False)

    orders = pagination.items
    if pagination.has_prev:
        prev = url_for('api.get_orders', status=status, page=page - 1, _external=True)

    if pagination.has_next:
        next = url_for('api.get_orders', status=status, page=page + 1, _external=True)
    
    return full_response(R200_OK, {
        'products': [order.to_json() for order in orders],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/orders/<string:rid>')
@auth.login_required
def get_order(rid):
    """订单详情"""
    order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    
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
    """
    新增订单

    :return: json
    """
    
    return "This is order create"


@api.route('/orders/delete', methods=['DELETE'])
@auth.login_required
def delete_order():
    """删除订单"""
    pass



