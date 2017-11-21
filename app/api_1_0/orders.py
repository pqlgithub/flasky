# -*- coding: utf-8 -*-
from . import api
from .utils import *


@api.route('/orders')
def orders():
    """
    订单列表

    :return: json
    """
    return "This is orders list."


@api.route('/orders/create', methods=['POST'])
def create_order():
    """
    新增订单
    
    :return: json
    """
    
    return "This is order create"