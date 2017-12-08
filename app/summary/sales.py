# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from app import db
from app.models import Order, OrderItem, ProductSku, MasterStatistics, StoreStatistics

class OrderDeal(object):
    """ 订单触发的相关数据统计 """
    
    def __init__(self, order_id):
        # 订单对象
        self.order_obj = Order.query.filter_by(id=order_id).first()
        
        # 订单明细列表
        self.items_obj_list = self.order_obj.items

        # 订单支付金额
        self.income = float(self.order_obj.pay_amount)
        # 该订单利润金额
        self.profit = 0.0
        for item in self.items_obj_list:
            sku = ProductSku.query.filter_by(id=item.sku_id).first()
            self.profit += round((float(item.deal_price) - float(sku.cost_price))
                            * item.quantity - float(item.discount_amount), 2)

        created_at = datetime.fromtimestamp(self.order_obj.created_at)
        # 该订单创建年份
        self.year = created_at.strftime("%Y")
        # 创建月份
        self.month = created_at.strftime("%Y%m")
        # 上一年
        self.last_year = (str)(created_at.year - 1)
        # 上一月
        self.last_month = (created_at - timedelta(days=created_at.day)
                      ).strftime("%Y%m")
        # 上年同一月
        self.last_year_month = self.last_year + str(created_at.month)


    def order_pay(self):
        """主账户、各店铺 销售订单付款统计"""

        try:
            # 主账户按年统计处理
            self.__master_year()
            # 主账户按月统计处理
            self.__master_year()
            # 子账户按年统计处理
            self.__store_year
            # 子账户按月统计处理
            self.__store_month

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise


    def __master_year(self):
        """主账户按年统计处理"""
        master_statistics_last_year = MasterStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.last_year, type=2).first()
        master_statistics_year = MasterStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.year, type=2).first()
        if master_statistics_year == None:
            # 如果有同比数据
            if master_statistics_last_year != None:
                # 销售同比
                income_yoy = round(
                    income / float(master_statistics_last_year.income) * 100, 2)
                # 利润同比
                profit_yoy = round(
                    profit / float(master_statistics_last_year.profit) * 100, 2)
            else:
                income_yoy = None
                profit_yoy = None

            master_statistics = MasterStatistics(
                master_uid=self.order_obj.master_uid,
                time=self.year,
                type=2,
                income=income,
                profit=profit,
                income_yoy=income_yoy,
                profit_yoy=profit_yoy,
            )
            db.session.add(master_statistics)
        else:
            master_statistics_year.income = float(master_statistics_year.income) + income
            master_statistics_year.profit = float(master_statistics_year.profit) + profit
            if master_statistics_last_year != None:
                # 销售同比
                master_statistics_year.income_yoy = round(
                    master_statistics_year.income / float(master_statistics_last_year.income) * 100, 2)
                # 利润同比
                master_statistics_year.profit_yoy = round(
                    master_statistics_year.profit / float(master_statistics_last_year.profit) * 100, 2)

    
    def __master_month(self):
        """主账户按月统计处理"""

        master_statistics_last_month = MasterStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.last_month, type=1).first()

        master_statistics_last_year_month = MasterStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.last_year_month, type=1).first()

        master_statistics_month = MasterStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.month, type=1).first()

        if master_statistics_month == None:
            # 如果有同比数据
            if master_statistics_last_year_month != None:
                # 销售同比
                income_yoy = round(
                    income / float(master_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                profit_yoy = round(
                    profit / float(master_statistics_last_year_month.profit) * 100, 2)
            else:
                income_yoy = None
                profit_yoy = None

            # 如果有环比数据
            if master_statistics_last_month != None:
                # 销售环比
                income_mom = round(
                    income / float(master_statistics_last_month.income) * 100, 2)
                # 利润环比
                profit_mom = round(
                    profit / float(master_statistics_last_month.profit) * 100, 2)
            else:
                income_mom = None
                profit_mom = None

            master_statistics = MasterStatistics(
                master_uid=self.order_obj.master_uid,
                time=self.month,
                type=1,
                income=income,
                profit=profit,
                income_yoy=income_mom,
                profit_yoy=profit_mom,
            )
            db.session.add(master_statistics)
        else:
            master_statistics_month.income = float(
                master_statistics_month.income) + income
            master_statistics_month.profit = float(
                master_statistics_month.profit) + profit
            if master_statistics_last_year_month != None:
                # 销售同比
                master_statistics_month.income_yoy = round(
                    master_statistics_month.income / float(master_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                master_statistics_month.profit_yoy = round(
                    master_statistics_month.profit / float(master_statistics_last_year_month.profit) * 100, 2)

            if master_statistics_last_month != None:
                # 销售环比
                master_statistics_month.income_mom = round(
                    master_statistics_month.income / float(master_statistics_last_month.income) * 100, 2)
                # 利润环比
                master_statistics_month.profit_mom = round(
                    master_statistics_month.profit / float(master_statistics_last_month.profit) * 100, 2)


    def __store_year(self):
        """ 子账户按年统计处理"""
        store_statistics_last_year = StoreStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.last_year, store_id=self.order_obj.store_id, type=2).first()
        store_statistics_year = StoreStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, store_id=self.order_obj.store_id, time=self.year, type=2).first()
        if store_statistics_year == None:
            # 如果有同比数据
            if store_statistics_last_year != None:
                # 销售同比
                income_yoy = round(
                    income / float(store_statistics_last_year.income) * 100, 2)
                # 利润同比
                profit_yoy = round(
                    profit / float(store_statistics_last_year.profit) * 100, 2)
            else:
                income_yoy = None
                profit_yoy = None

            store_statistics = StoreStatistics(
                master_uid=self.order_obj.master_uid,
                store_id=self.order_obj.store_id,
                time=self.year,
                type=2,
                income=income,
                profit=profit,
                income_yoy=income_yoy,
                profit_yoy=profit_yoy,
            )
            db.session.add(store_statistics)
        else:
            store_statistics_year.income = float(
                store_statistics_year.income) + income
            store_statistics_year.profit = float(
                store_statistics_year.profit) + profit
            if store_statistics_last_year != None:
                # 销售同比
                store_statistics_year.income_yoy = round(
                    store_statistics_year.income / float(store_statistics_last_year.income) * 100, 2)
                # 利润同比
                store_statistics_year.profit_yoy = round(
                    store_statistics_year.profit / float(store_statistics_last_year.profit) * 100, 2)


    def __store_month(self):
        """ 子账户按月统计处理 """
        store_statistics_last_month = StoreStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.last_month, store_id=self.order_obj.store_id, type=1).first()

        store_statistics_last_year_month = StoreStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.last_year_month, store_id=self.order_obj.store_id, type=1).first()

        store_statistics_month = StoreStatistics.query.filter_by(
            master_uid=self.order_obj.master_uid, time=self.month, store_id=self.order_obj.store_id, type=1).first()

        if store_statistics_month == None:
            # 如果有同比数据
            if store_statistics_last_year_month != None:
                # 销售同比
                income_yoy = round(
                    income / float(store_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                profit_yoy = round(
                    profit / float(store_statistics_last_year_month.profit) * 100, 2)
            else:
                income_yoy = None
                profit_yoy = None

            # 如果有环比数据
            if store_statistics_last_month != None:
                # 销售环比
                income_mom = round(
                    income / float(store_statistics_last_month.income) * 100, 2)
                # 利润环比
                profit_mom = round(
                    profit / float(store_statistics_last_month.profit) * 100, 2)
            else:
                income_mom = None
                profit_mom = None

            store_statistics = StoreStatistics(
                master_uid=self.order_obj.master_uid,
                store_id=self.order_obj.store_id,
                time=self.month,
                type=1,
                income=income,
                profit=profit,
                income_yoy=income_mom,
                profit_yoy=profit_mom,
            )
            db.session.add(store_statistics)
        else:
            store_statistics_month.income = float(
                store_statistics_month.income) + income
            store_statistics_month.profit = float(
                store_statistics_month.profit) + profit
            if store_statistics_last_year_month != None:
                # 销售同比
                store_statistics_month.income_yoy = round(
                    store_statistics_month.income / float(store_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                store_statistics_month.profit_yoy = round(
                    store_statistics_month.profit / float(store_statistics_last_year_month.profit) * 100, 2)

            if store_statistics_last_month != None:
                # 销售环比
                store_statistics_month.income_mom = round(
                    store_statistics_month.income / float(store_statistics_last_month.income) * 100, 2)
                # 利润环比
                store_statistics_month.profit_mom = round(
                    store_statistics_month.profit / float(store_statistics_last_month.profit) * 100, 2)




