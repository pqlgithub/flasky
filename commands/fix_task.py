# -*- coding: utf-8 -*-
from flask_script import Command
from app.models import Order


class FixTask(Command):
    """Task to fix data of system """

    def run(self):
        self.rebuild_order_stats()

    def rebuild_order_stats(self):
        from app.tasks import sales_stats

        orders = Order.query.all()

        for order in orders:
            sales_stats.delay(order.id)
