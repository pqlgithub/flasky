# -*- coding: utf-8 -*-
from flask import render_template, current_app

from . import distribute
from app.models import Customer, Order


@distribute.route('/orders')
def show_orders():
    """订单列表"""
    pass

