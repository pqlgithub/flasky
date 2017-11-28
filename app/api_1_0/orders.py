# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from app.models import User, Product

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/orders')
@auth.login_required
def get_orders():
    """
    订单列表

    :return: json
    """
    return "This is orders list."



@api.route('/orders/<string:rid>')
@auth.login_required
def get_order(rid):
    """订单详情"""
    pass


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



