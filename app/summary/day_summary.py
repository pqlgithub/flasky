# -*- coding: utf-8 -*-
from app import db
from app.models import SalesLogStatistics, DaySkuStatistics
from datetime import datetime


class DaySummary(object):
    def __init__(self, order_id):
        self.sales_logs = SalesLogStatistics.query.filter_by(
            order_id=order_id).all()

    def pay_run(self):
        self.__action(self.__add)

    def refund_run(self):
        self.__action(self.__delete)

    def __action(self, func):
        sales_day = None
        for sales_log in self.sales_logs:
            income = round(float(sales_log.deal_price) * sales_log.quantity -
                           float(sales_log.discount_amount), 2)
            profit = round(income -
                           (float(sales_log.cost_price) * sales_log.quantity), 2)
            if sales_day is None:
                sales_datetime = datetime.fromtimestamp(sales_log.create_at)
                sales_day = int(
                    datetime(sales_datetime.year, sales_datetime.month,
                             sales_datetime.day).timestamp())
            func(sales_log, income, profit, sales_day)

    def __add(self, sales_log, income, profit, sales_day):
        day_sku = DaySkuStatistics.query.filter_by(
            store_id=sales_log.store_id,
            sku_id=sales_log.sku_id,
            time=sales_day).first()

        if day_sku is None:
            day_sku = DaySkuStatistics(
                master_uid=sales_log.master_uid,
                store_id=sales_log.store_id,
                product_id=sales_log.product_id,
                sku_id=sales_log.sku_id,
                sku_serial_no=sales_log.sku_serial_no,
                category_id=sales_log.category_id,
                supplier_id=sales_log.supplier_id,
                income=income,
                profit=profit,
                time=sales_day)
            db.session.add(day_sku)
        else:
            day_sku.income = float(day_sku.income) + income
            day_sku.profit = float(day_sku.profit) + income

    def __delete(self, sales_log, income, profit, sales_day):
        day_sku = DaySkuStatistics.query.filter_by(
            store_id=sales_log.store_id,
            sku_id=sales_log.sku_id,
            time=sales_day).first()

        if day_sku is None:
            pass
        else:
            day_sku.income = float(day_sku.income) - income
            day_sku.profit = float(day_sku.profit) - income
