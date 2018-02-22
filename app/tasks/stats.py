# -*- coding: utf-8 -*-
from flask import current_app
from app.extensions import fsk_celery

from app import db
from app.models import Currency, Site
from app.summary import StoreSales, StoreProductSales, SalesLog


@fsk_celery.task
def sales_statistics(order_id):
    SalesLog(order_id).order_pay()

    # 订单付款时 主账户、各店铺及sku 销售统计
    StoreSales(order_id).order_pay()
    StoreProductSales(order_id).order_pay()


@fsk_celery.task
def refund_statistics(order_id):
    SalesLog(order_id).order_refund()

    # 订单退款时 主账户、各店铺及sku 销售统计
    StoreSales(order_id).order_refund()
    StoreProductSales(order_id).order_refund()
