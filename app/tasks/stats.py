# -*- coding: utf-8 -*-
from app.extensions import fsk_celery
from app.summary import StoreSales, StoreProductSales, SalesLog


@fsk_celery.task(name='stats.sales_stats')
def sales_stats(order_id):
    """订单支付后触发任务"""

    # 销售统计
    SalesLog(order_id).order_pay()

    # 订单付款时, 主账户、各店铺及sku 销售统计
    StoreSales(order_id).order_pay()

    # 店铺商品销售汇总
    StoreProductSales(order_id).order_pay()


@fsk_celery.task(name='stats.refund_stats')
def refund_stats(order_id):
    """订单退款后重新汇总"""

    # 销售退款
    SalesLog(order_id).order_refund()

    # 订单退款时 主账户、各店铺及sku 销售统计
    StoreSales(order_id).order_refund()

    StoreProductSales(order_id).order_refund()
