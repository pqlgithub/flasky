# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from app.exceptions import ValidationError


class FxFilter(object):
    """
    API过滤拦截器，根据不同级别过滤成本价、库存等敏感信息
    """

    @staticmethod
    def product_data(row, fields=('cost_price', 'stock_count')):
        """商品相关数据"""

        if not fields:
            raise ValidationError('Fields is Null!')

        some_row = {}
        for key in row.keys():
            if key not in fields:
                some_row[key] = row[key]

        return some_row

    @staticmethod
    def order_data():
        """订单相关数据"""
        pass

