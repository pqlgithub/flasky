# -*- coding: utf-8 -*-
from flask import render_template, current_app
from . import distribute


@distribute.route('/products')
def show_products():
    """商品列表"""
    pass


@distribute.route('/products/create')
def create_product():
    """添加商品"""
    pass
