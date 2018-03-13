# -*- coding: utf-8 -*-
from app import db
from app.models import Order, SalesLogStatistics


class SalesLog(object):

    def __init__(self, order_id):
        self.order_id = order_id
        # 订单对象
        self.order = Order.query.filter_by(id=order_id).first()
        # 主账户ID
        self.master_uid = self.order.master_uid
        # 店铺ID
        self.store_id = self.order.store_id

        self.created_at = self.order.created_at

    def order_pay(self):
        from .day_summary import DaySummary
        try:
            for item in self.order.items:
                self.__item_log_save(item)

            # 销售记录表生成后 对销售记录各个维度按天进行统计
            # sku销售统计
            DaySummary(self.order_id).pay_run()

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def order_refund(self):
        from .day_summary import DaySummary
        try:
            sales_logs = SalesLogStatistics.query.filter_by(order_id=self.order_id).all()
            for item in sales_logs:
                item.status = -1
               
            # 销售记录表修改后 对销售记录各个维度按天统计进行修改
            # sku销售统计
            DaySummary(self.order_id).refund_run()

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def __item_log_save(self, item):
        sku = item.sku
        product = sku.product
        category_ids = product.category_ids

        sales_log_statistics = SalesLogStatistics(
            master_uid=self.master_uid,
            store_id=self.store_id,
            order_id=self.order_id,
            sku_id=item.sku_id,
            product_id=sku.product_id,
            sku_serial_no=item.sku_serial_no,
            deal_price=item.deal_price,
            cost_price=sku.cost_price,
            quantity=item.quantity,
            discount_amount=item.discount_amount,
            create_at=self.created_at,
            status=1,
            category_id=category_ids[0],
            supplier_id=product.supplier_id,
        )

        db.session.add(sales_log_statistics)
