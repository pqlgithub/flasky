import sys
from flask import current_app
from flask_script import Command
from app import db
from app.models import Order, OrderStatus


class InitSummary(Command):
    """
    初始化统计数据：
        将清空统计相关表，根据sales_log_statistics统计表从新统计
    """

    def run(self):
        print("start runing...")
        # 清空统计相关数据表
        self.delete_table()
        # 发送统计队列任务
        self.send_order_id()
        print("end")

    def delete_table(self):
        """ 
        清空统计相关数据表
        """
        tables = ('sales_log_statistics', 'day_sku_statistics',
                  'master_statistics', 'store_statistics',
                  'product_statistics')

        for name in tables:
            sql = "truncate table %s" % name
            db.engine.execute(sql)

    def send_order_id(self):
        """
        发送统计队列任务
        """
        # 初始ID
        blank = 1000
        start_number = 0
        end_number = start_number + blank
        while True:
            order_ids = db.session.query(
                Order.id).filter(Order.id >= start_number).filter(
                    Order.id < end_number
                ).filter(Order.status != OrderStatus.CANCELED).filter(
                    Order.status != OrderStatus.PENDING_PAYMENT).filter(
                        Order.status != OrderStatus.REFUND).all()
            
            if not order_ids:
                break

            for order in order_ids:
                # tasks.sales_statistics.delay(order.id)
                pass

            start_number = end_number
            end_number = start_number + blank
            print("runing: %d" % start_number)
