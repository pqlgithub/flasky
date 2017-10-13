# -*- coding: utf-8 -*-

import sys
from flask import current_app
from flask_script import Command
from app import db
from app.models import Product, ProductSku


class FixData(Command):
    """fix data of system"""

    def run(self):
        """修正产品sku区域问题"""
        products = Product.query.all()
        for product in products:
            region_id = product.region_id
            for sku in product.skus:
                sku.region_id = region_id
                print('update sku[%s]' % sku.serial_no)
            
        db.session.commit()