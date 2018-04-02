# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from . import main
from .. import db
from app.models import Order, Product, ProductStock, Site
from ..utils import Master
from ..decorators import user_has, user_is


@main.route('/dashboard')
@user_has('admin_dashboard')
def index():
    # 统计数量
    total_product_count = Product.query.filter_by(master_uid=Master.master_uid()).count()
    # 最新的1个产品
    new_products = Product.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').first()

    # 当前库存总数
    builder = ProductStock.query.filter_by(master_uid=Master.master_uid())
    total_stock_quantity = builder.with_entities(func.sum(ProductStock.current_count)).one()

    # 订单总数
    total_order_count = Order.query.filter_by(master_uid=Master.master_uid()).count()
    # 最近的10个订单
    top_orders = Order.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').limit(10).all()

    # 总收入
    total_revenue = Order.query.filter_by(master_uid=Master.master_uid())\
        .with_entities(func.sum(Order.pay_amount)).one()

    return render_template('dashboard/index.html',
                           top_menu='dashboard',
                           top_orders=top_orders,
                           total_revenue=total_revenue,
                           total_order_count=total_order_count,
                           new_products=new_products,
                           total_product_count=total_product_count,
                           total_stock_quantity=total_stock_quantity)