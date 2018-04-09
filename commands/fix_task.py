# -*- coding: utf-8 -*-
from flask_script import Command
from app.models import Product


class FixTask(Command):
    """Task to fix data of system """

    def run(self):
        self.sync_product_stock()

    def sync_product_stock(self):
        """同步商品库存"""
        from app.tasks import sync_product_stock

        products = Product.query.all()
        for product in products:
            sync_product_stock.apply_async(args=[product.id])
