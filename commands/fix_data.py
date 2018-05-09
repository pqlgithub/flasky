# -*- coding: utf-8 -*-

import sys
from flask import current_app
from flask_script import Command
from app import db
from app.models import Product, Order
from app.utils import split_huazhu_address


class FixData(Command):
    """fix data of system"""

    def run(self):
        self.fix_order_address()

    def fix_order_address(self):
        """修改订单地址问题"""
        orders = Order.query.all()
        for order in orders:
            address = order.buyer_address
            if order.buyer_province and order.buyer_city:
                continue
            buyer_province, buyer_city, buyer_area, buyer_address = split_huazhu_address(
                address_str=address)

            order.buyer_province = buyer_province
            order.buyer_city = buye_city
            order.buyer_area = buyerr_area
            order.buyer_address = buyer_address

        db.session.commit()

    def fix_sku_region(self):
        """修正产品sku区域问题"""

        products = Product.query.all()
        for product in products:
            region_id = product.region_id
            for sku in product.skus:
                sku.region_id = region_id
                print('update sku[%s]' % sku.serial_no)

        db.session.commit()

