# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from app import db
from app.models import Order, OrderItem, ProductSku, MasterStatistics, StoreStatistics, ProductStatistics


class Sales(object):
    def __init__(self, order_id):
        # 订单对象
        self.order_obj = Order.query.filter_by(id=order_id).first()
        # 主账户ID
        self.master_uid = self.order_obj.master_uid
        # 店铺ID
        self.store_id = self.order_obj.store_id
        # 订单明细列表
        self.items_obj_list = self.order_obj.items

        created_at = datetime.fromtimestamp(self.order_obj.created_at)
        # 该订单创建年份
        self.year = created_at.strftime("%Y")
        # 创建月份
        self.month = created_at.strftime("%Y%m")
        # 上一年
        self.last_year = str(created_at.year - 1)
        # 上一月
        self.last_month = (
            created_at - timedelta(days=created_at.day)).strftime("%Y%m")
        # 上年同一月
        self.last_year_month = self.last_year + str(created_at.month)


class StoreSales(Sales):
    """ 订单触发的店铺收入、利润相关数据统计 """

    def __init__(self, order_id):
        super().__init__(order_id)

        # 订单支付金额
        self.income = float(self.order_obj.pay_amount)
        # 该订单利润金额
        self.profit = 0.0
        for item in self.items_obj_list:
            sku = ProductSku.query.filter_by(id=item.sku_id).first()
            self.profit += round(
                (float(item.deal_price) - float(sku.cost_price)) *
                item.quantity - float(item.discount_amount), 2)

    def order_pay(self):
        """订单付款时 主账户、各店铺 销售订单付款统计"""

        try:
            # 主账户按年统计处理
            self.__master_year()
            # 主账户按月统计处理
            self.__master_month()
            # 子账户按年统计处理
            self.__store_year()
            # 子账户按月统计处理
            self.__store_month()

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def order_refund(self):
        """ 订单退款时主账户、各店铺  收入、利润、收入同比、利润同比统计"""
        try:
            # 退款时主账户按年统计处理
            self.__refund_master_year()
            # 退款时主账户按月统计处理
            self.__refund_master_month()
            # 退款时子账户按年统计处理
            self.__refund_store_year()
            # 退款时子账户按月统计处理
            self.__refund_store_month()

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def __master_year(self):
        """主账户按年统计处理 收入、利润、收入同比、利润同比"""
        master_statistics_last_year = MasterStatistics.query.filter_by(
            master_uid=self.master_uid, time=self.last_year, type=2).first()
        # 查询加独占锁
        master_statistics_year = MasterStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid, time=self.year, type=2).first()
        if master_statistics_year == None:
            # 如果有同比数据
            if master_statistics_last_year != None:
                # 销售同比
                income_yoy = round(
                    self.income / float(master_statistics_last_year.income) * 100,
                    2)
                # 利润同比
                profit_yoy = round(
                    self.profit / float(master_statistics_last_year.profit) * 100,
                    2)
            else:
                income_yoy = None
                profit_yoy = None

            master_statistics = MasterStatistics(
                master_uid=self.master_uid,
                time=self.year,
                type=2,
                income=self.income,
                profit=self.profit,
                income_yoy=income_yoy,
                profit_yoy=profit_yoy,
            )
            db.session.add(master_statistics)
        else:
            master_statistics_year.income = float(
                master_statistics_year.income) + self.income
            master_statistics_year.profit = float(
                master_statistics_year.profit) + self.profit
            if master_statistics_last_year != None:
                # 销售同比
                master_statistics_year.income_yoy = round(
                    master_statistics_year.income / float(
                        master_statistics_last_year.income) * 100, 2)
                # 利润同比
                master_statistics_year.profit_yoy = round(
                    master_statistics_year.profit / float(
                        master_statistics_last_year.profit) * 100, 2)

    def __master_month(self):
        """主账户按月统计处理"""

        master_statistics_last_month = MasterStatistics.query.filter_by(
            master_uid=self.master_uid, time=self.last_month, type=1).first()

        master_statistics_last_year_month = MasterStatistics.query.filter_by(
            master_uid=self.master_uid, time=self.last_year_month,
            type=1).first()

        master_statistics_month = MasterStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid, time=self.month, type=1).first()

        if master_statistics_month == None:
            # 如果有同比数据
            if master_statistics_last_year_month != None:
                # 销售同比
                income_yoy = round(self.income / float(
                    master_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                profit_yoy = round(self.profit / float(
                    master_statistics_last_year_month.profit) * 100, 2)
            else:
                income_yoy = None
                profit_yoy = None

            # 如果有环比数据
            if master_statistics_last_month != None:
                # 销售环比
                income_mom = round(
                    self.income / float(master_statistics_last_month.income) * 100,
                    2)
                # 利润环比
                profit_mom = round(
                    self.profit / float(master_statistics_last_month.profit) * 100,
                    2)
            else:
                income_mom = None
                profit_mom = None

            master_statistics = MasterStatistics(
                master_uid=self.master_uid,
                time=self.month,
                type=1,
                income=self.income,
                profit=self.profit,
                income_yoy=income_mom,
                profit_yoy=profit_mom,
            )
            db.session.add(master_statistics)
        else:
            master_statistics_month.income = float(
                master_statistics_month.income) + self.income
            master_statistics_month.profit = float(
                master_statistics_month.profit) + self.profit
            if master_statistics_last_year_month != None:
                # 销售同比
                master_statistics_month.income_yoy = round(
                    master_statistics_month.income / float(
                        master_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                master_statistics_month.profit_yoy = round(
                    master_statistics_month.profit / float(
                        master_statistics_last_year_month.profit) * 100, 2)

            if master_statistics_last_month != None:
                # 销售环比
                master_statistics_month.income_mom = round(
                    master_statistics_month.income / float(
                        master_statistics_last_month.income) * 100, 2)
                # 利润环比
                master_statistics_month.profit_mom = round(
                    master_statistics_month.profit / float(
                        master_statistics_last_month.profit) * 100, 2)

    def __store_year(self):
        """ 子账户按年统计处理"""
        store_statistics_last_year = StoreStatistics.query.filter_by(
            master_uid=self.master_uid,
            time=self.last_year,
            store_id=self.store_id,
            type=2).first()
        store_statistics_year = StoreStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid,
            store_id=self.store_id,
            time=self.year,
            type=2).first()
        if store_statistics_year == None:
            # 如果有同比数据
            if store_statistics_last_year != None:
                # 销售同比
                income_yoy = round(
                    self.income / float(store_statistics_last_year.income) * 100, 2)
                # 利润同比
                profit_yoy = round(
                    self.profit / float(store_statistics_last_year.profit) * 100, 2)
            else:
                income_yoy = None
                profit_yoy = None

            store_statistics = StoreStatistics(
                master_uid=self.master_uid,
                store_id=self.store_id,
                time=self.year,
                type=2,
                income=self.income,
                profit=self.profit,
                income_yoy=income_yoy,
                profit_yoy=profit_yoy,
            )
            db.session.add(store_statistics)
        else:
            store_statistics_year.income = float(
                store_statistics_year.income) + self.income
            store_statistics_year.profit = float(
                store_statistics_year.profit) + self.profit
            if store_statistics_last_year != None:
                # 销售同比
                store_statistics_year.income_yoy = round(
                    store_statistics_year.income / float(
                        store_statistics_last_year.income) * 100, 2)
                # 利润同比
                store_statistics_year.profit_yoy = round(
                    store_statistics_year.profit / float(
                        store_statistics_last_year.profit) * 100, 2)

    def __store_month(self):
        """ 子账户按月统计处理 """
        store_statistics_last_month = StoreStatistics.query.filter_by(
            master_uid=self.master_uid,
            time=self.last_month,
            store_id=self.store_id,
            type=1).first()

        store_statistics_last_year_month = StoreStatistics.query.filter_by(
            master_uid=self.master_uid,
            time=self.last_year_month,
            store_id=self.store_id,
            type=1).first()

        store_statistics_month = StoreStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid,
            time=self.month,
            store_id=self.store_id,
            type=1).first()

        if store_statistics_month == None:
            # 如果有同比数据
            if store_statistics_last_year_month != None:
                # 销售同比
                income_yoy = round(self.income / float(
                    store_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                profit_yoy = round(self.profit / float(
                    store_statistics_last_year_month.profit) * 100, 2)
            else:
                income_yoy = None
                profit_yoy = None

            # 如果有环比数据
            if store_statistics_last_month != None:
                # 销售环比
                income_mom = round(
                    self.income / float(store_statistics_last_month.income) * 100,
                    2)
                # 利润环比
                profit_mom = round(
                    self.profit / float(store_statistics_last_month.profit) * 100,
                    2)
            else:
                income_mom = None
                profit_mom = None

            store_statistics = StoreStatistics(
                master_uid=self.master_uid,
                store_id=self.store_id,
                time=self.month,
                type=1,
                income=self.income,
                profit=self.profit,
                income_yoy=income_mom,
                profit_yoy=profit_mom,
            )
            db.session.add(store_statistics)
        else:
            store_statistics_month.income = float(
                store_statistics_month.income) + self.income
            store_statistics_month.profit = float(
                store_statistics_month.profit) + self.profit
            if store_statistics_last_year_month != None:
                # 销售同比
                store_statistics_month.income_yoy = round(
                    store_statistics_month.income / float(
                        store_statistics_last_year_month.income) * 100, 2)
                # 利润同比
                store_statistics_month.profit_yoy = round(
                    store_statistics_month.profit / float(
                        store_statistics_last_year_month.profit) * 100, 2)

            if store_statistics_last_month != None:
                # 销售环比
                store_statistics_month.income_mom = round(
                    store_statistics_month.income / float(
                        store_statistics_last_month.income) * 100, 2)
                # 利润环比
                store_statistics_month.profit_mom = round(
                    store_statistics_month.profit / float(
                        store_statistics_last_month.profit) * 100, 2)

    def __refund_master_year(self):
        """退款时主账户按年统计处理"""
        master_statistics_last_year = MasterStatistics.query.filter_by(
            master_uid=self.master_uid, time=self.last_year, type=2).first()
        master_statistics_year = MasterStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid, time=self.year, type=2).first()

        master_statistics_year.income = float(
            master_statistics_year.income) - self.income
        master_statistics_year.profit = float(
            master_statistics_year.profit) - self.profit
        if master_statistics_last_year != None:
            # 销售同比
            master_statistics_year.income_yoy = round(
                master_statistics_year.income / float(
                    master_statistics_last_year.income) * 100, 2)
            # 利润同比
            master_statistics_year.profit_yoy = round(
                master_statistics_year.profit / float(
                    master_statistics_last_year.profit) * 100, 2)

    def __refund_master_year(self):
        """退款时主账户按月统计处理"""
        master_statistics_last_month = MasterStatistics.query.filter_by(
            master_uid=self.master_uid, time=self.last_month, type=1).first()

        master_statistics_last_year_month = MasterStatistics.query.filter_by(
            master_uid=self.master_uid, time=self.last_year_month,
            type=1).first()

        master_statistics_month = MasterStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid, time=self.month, type=1).first()

        master_statistics_month.income = float(
            master_statistics_month.income) - self.income
        master_statistics_month.profit = float(
            master_statistics_month.profit) - self.profit

        if master_statistics_last_year_month != None:
            # 销售同比
            master_statistics_month.income_yoy = round(
                master_statistics_month.income / float(
                    master_statistics_last_year_month.income) * 100, 2)
            # 利润同比
            master_statistics_month.profit_yoy = round(
                master_statistics_month.profit / float(
                    master_statistics_last_year_month.profit) * 100, 2)

        if master_statistics_last_month != None:
            # 销售环比
            master_statistics_month.income_mom = round(
                master_statistics_month.income / float(
                    master_statistics_last_month.income) * 100, 2)
            # 利润环比
            master_statistics_month.profit_mom = round(
                master_statistics_month.profit / float(
                    master_statistics_last_month.profit) * 100, 2)

    def __refund_store_year(self):
        """退款时子账户按年统计处理"""
        store_statistics_last_year = StoreStatistics.query.filter_by(
            master_uid=self.master_uid,
            time=self.last_year,
            store_id=self.store_id,
            type=2).first()
        store_statistics_year = StoreStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid,
            store_id=self.store_id,
            time=self.year,
            type=2).first()

        store_statistics_year.income = float(
            store_statistics_year.income) - self.income
        store_statistics_year.profit = float(
            store_statistics_year.profit) - self.profit
        if store_statistics_last_year != None:
            # 销售同比
            store_statistics_year.income_yoy = round(
                store_statistics_year.income / float(
                    store_statistics_last_year.income) * 100, 2)
            # 利润同比
            store_statistics_year.profit_yoy = round(
                store_statistics_year.profit / float(
                    store_statistics_last_year.profit) * 100, 2)

    def __refund_store_month(self):
        """退款时子账户按月统计处理"""
        store_statistics_last_month = StoreStatistics.query.filter_by(
            master_uid=self.master_uid,
            time=self.last_month,
            store_id=self.store_id,
            type=1).first()

        store_statistics_last_year_month = StoreStatistics.query.filter_by(
            master_uid=self.master_uid,
            time=self.last_year_month,
            store_id=self.store_id,
            type=1).first()

        store_statistics_month = StoreStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid,
            time=self.month,
            store_id=self.store_id,
            type=1).first()

        store_statistics_month.income = float(
            store_statistics_month.income) - self.income
        store_statistics_month.profit = float(
            store_statistics_month.profit) - self.profit
        if store_statistics_last_year_month != None:
            # 销售同比
            store_statistics_month.income_yoy = round(
                store_statistics_month.income / float(
                    store_statistics_last_year_month.income) * 100, 2)
            # 利润同比
            store_statistics_month.profit_yoy = round(
                store_statistics_month.profit / float(
                    store_statistics_last_year_month.profit) * 100, 2)

        if store_statistics_last_month != None:
            # 销售环比
            store_statistics_month.income_mom = round(
                store_statistics_month.income / float(
                    store_statistics_last_month.income) * 100, 2)
            # 利润环比
            store_statistics_month.profit_mom = round(
                store_statistics_month.profit / float(
                    store_statistics_last_month.profit) * 100, 2)


class StoreProductSales(Sales):
    """主账户、下属店铺 各商品销售统计"""

    def __init__(self, order_id):
        super().__init__(order_id)

        # 订单明细中 sku_id、金额、利润、数量的dict 列表
        self.sku_price_count = []
        for item in self.items_obj_list:
            sku = ProductSku.query.filter_by(id=item.sku_id).first()
            data = {}
            data['sku_id'] = item.sku_id
            data['sku_serial_no'] = item.sku_serial_no
            data['income'] = round(float(item.deal_price) * item.quantity, 2)
            data['profit'] = round(
                (float(item.deal_price) - float(sku.cost_price)) *
                item.quantity - float(item.discount_amount), 2)
            data['count'] = item.quantity
            self.sku_price_count.append(data)

    def order_pay(self):
        """订单付款时 主账户、下属店铺 sku销售统计"""
        try:
            self.__master_year()
            self.__master_month()
            self.__store_year()
            self.__store_month()

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def order_refund(self):
        """订单退款时 主账户、下属店铺 sku销售统计"""
        try:
            self.__refund_master_year()
            self.__refund_master_month()
            self.__refund_store_year()
            self.__refund_store_month()

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def __get_product_master(self, sku_id, time_type, date):
        """
        获取主账户的销售统计模型
        Args: 
            sku_id: skuID。
            time_type: 时间类型：1.月  2.年。
            date: 具体时间 如：(2017、201702)。

        Returns:
            数据模型 | None.
        """
        product_master = ProductStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid,
            time=date,
            time_type=time_type,
            type=1,  # 主账户
            sku_id=sku_id,
        ).first()
        return product_master

    def __get_product_store(self, sku_id, time_type, date):
        """
        获取下属店铺的销售统计模型
        Args: 
            sku_id: skuID
            time_type: 时间类型：1.月  2.年
            date: 具体时间 如：(2017、201702）

        Returns:
            数据模型 | None
        """
        product_store = ProductStatistics.query.with_for_update(read=False).filter_by(
            master_uid=self.master_uid,
            store_id=self.store_id,
            time=date,
            time_type=time_type,
            type=2,  # 下属店铺
            sku_id=sku_id,
        ).first()
        return product_store

    def __master_year(self):
        """主账户下sku 按年销售统计"""
        for v in self.sku_price_count:
            product_master_year = self.__get_product_master(
                v['sku_id'], 2, self.year)
            product_master_last_year = self.__get_product_master(
                v['sku_id'], 2, self.last_year)

            if product_master_year == None:
                if product_master_last_year != None:
                    # 销售同比
                    income_yoy = round(v['income'] / float(
                        product_master_last_year.income) * 100, 2)
                    # 利润同比
                    profit_yoy = round(v['profit'] / float(
                        product_master_last_year.profit) * 100, 2)
                else:
                    income_yoy = None
                    profit_yoy = None

                product_master_statistics = ProductStatistics(
                    master_uid=self.master_uid,
                    sku_id=v['sku_id'],
                    sku_serial_no=v['sku_serial_no'],
                    time=self.year,
                    time_type=2,
                    type=1,
                    income=v['income'],
                    profit=v['profit'],
                    count=v['count'],
                    income_yoy=income_yoy,
                    profit_yoy=profit_yoy,
                )

                db.session.add(product_master_statistics)
            else:
                product_master_year.income = float(
                    product_master_year.income) + v['income']
                product_master_year.profit = float(
                    product_master_year.profit) + v['profit']
                product_master_year.count = float(
                    product_master_year.count) + v['count']
                if product_master_last_year != None:
                    # 销售同比
                    product_master_year.income_yoy = round(
                        product_master_year.income / float(
                            product_master_last_year.income) * 100, 2)
                    # 利润同比
                    product_master_year.profit_yoy = round(
                        product_master_year.profit / float(
                            product_master_last_year.profit) * 100, 2)

    def __master_month(self):
        """主账户 sku按月销售统计"""
        for v in self.sku_price_count:
            product_master_month = self.__get_product_master(
                v['sku_id'], 1, self.month)
            product_master_last_month = self.__get_product_master(
                v['sku_id'], 1, self.last_month)
            product_master_last_year_month = self.__get_product_master(
                v['sku_id'], 1, self.last_year_month)

            if product_master_month == None:
                # 如果有同比数据
                if product_master_last_year_month != None:
                    # 销售同比
                    income_yoy = round(v['income'] / float(
                        product_master_last_year_month.income) * 100, 2)
                    # 利润同比
                    profit_yoy = round(v['profit'] / float(
                        product_master_last_year_month.profit) * 100, 2)
                else:
                    income_yoy = None
                    profit_yoy = None

                # 如果有环比数据
                if product_master_last_month != None:
                    # 销售环比
                    income_mom = round(v['income'] / float(
                        product_master_last_month.income) * 100, 2)
                    # 利润环比
                    profit_mom = round(v['profit'] / float(
                        product_master_last_month.profit) * 100, 2)
                else:
                    income_mom = None
                    profit_mom = None

                product_master = ProductStatistics(
                    master_uid=self.master_uid,
                    sku_id=v['sku_id'],
                    sku_serial_no=v['sku_serial_no'],
                    time=self.month,
                    time_type=1,  # month
                    type=1,  # master
                    income=v['income'],
                    profit=v['profit'],
                    count=v['count'],
                    income_yoy=income_yoy,
                    profit_yoy=profit_yoy,
                    income_mom=income_mom,
                    profit_mom=profit_mom,
                )
                db.session.add(product_master)
            else:
                product_master_month.income = float(
                    product_master_month.income) + v['income']
                product_master_month.profit = float(
                    product_master_month.profit) + v['profit']
                product_master_month.count = float(
                    product_master_month.count) + v['count']

                if product_master_last_year_month != None:
                    # 销售同比
                    product_master_month.income_yoy = round(
                        product_master_month.income / float(
                            product_master_last_year_month.income) * 100, 2)
                    # 利润同比
                    product_master_month.profit_yoy = round(
                        product_master_month.profit / float(
                            product_master_last_year_month.profit) * 100, 2)

                if product_master_last_month != None:
                    # 销售环比
                    product_master_month.income_mom = round(
                        product_master_month.income / float(
                            product_master_last_month.income) * 100, 2)
                    # 利润环比
                    product_master_month.profit_mom = round(
                        product_master_month.profit / float(
                            product_master_last_month.profit) * 100, 2)

    def __store_year(self):
        """下属店铺sku按年销售统计"""
        for v in self.sku_price_count:
            product_store_year = self.__get_product_store(
                v['sku_id'], 2, self.year)
            product_store_last_year = self.__get_product_store(
                v['sku_id'], 2, self.last_year)

            if product_store_year == None:
                if product_store_last_year != None:
                    # 销售同比
                    income_yoy = round(
                        v['income'] / float(product_store_last_year.income) * 100,
                        2)
                    # 利润同比
                    profit_yoy = round(
                        v['profit'] / float(product_store_last_year.profit) * 100,
                        2)
                else:
                    income_yoy = None
                    profit_yoy = None

                product_store_year = ProductStatistics(
                    master_uid=self.master_uid,
                    store_id=self.store_id,
                    sku_id=v['sku_id'],
                    sku_serial_no=v['sku_serial_no'],
                    time=self.year,
                    time_type=2,
                    type=2,
                    income=v['income'],
                    profit=v['profit'],
                    count=v['count'],
                    income_yoy=income_yoy,
                    profit_yoy=profit_yoy,
                )

                db.session.add(product_store_year)
            else:
                product_store_year.income = float(
                    product_store_year.income) + v['income']
                product_store_year.profit = float(
                    product_store_year.profit) + v['profit']
                product_store_year.count = float(
                    product_store_year.count) + v['count']

                if product_store_last_year != None:
                    # 销售同比
                    product_store_year.income_yoy = round(
                        product_store_year.income / float(
                            product_store_last_year.income) * 100, 2)
                    # 利润同比
                    product_store_year.profit_yoy = round(
                        product_store_year.profit / float(
                            product_store_last_year.profit) * 100, 2)

    def __store_month(self):
        """下属店铺sku按月销售统计"""
        for v in self.sku_price_count:
            product_store_month = self.__get_product_store(
                v['sku_id'], 1, self.month)
            product_store_last_month = self.__get_product_store(
                v['sku_id'], 1, self.last_month)
            product_store_last_year_month = self.__get_product_store(
                v['sku_id'], 1, self.last_year_month)

            if product_store_month == None:
                # 如果有同比数据
                if product_store_last_year_month != None:
                    # 销售同比
                    income_yoy = round(v['income'] / float(
                        product_store_last_year_month.income) * 100, 2)
                    # 利润同比
                    profit_yoy = round(v['profit'] / float(
                        product_store_last_year_month.profit) * 100, 2)
                else:
                    income_yoy = None
                    profit_yoy = None

                # 如果有环比数据
                if product_store_last_month != None:
                    # 销售环比
                    income_mom = round(v['income'] / float(
                        product_store_last_month.income) * 100, 2)
                    # 利润环比
                    profit_mom = round(v['profit'] / float(
                        product_store_last_month.profit) * 100, 2)
                else:
                    income_mom = None
                    profit_mom = None

                product_master = ProductStatistics(
                    master_uid=self.master_uid,
                    store_id=self.store_id,
                    sku_id=v['sku_id'],
                    sku_serial_no=v['sku_serial_no'],
                    time=self.month,
                    time_type=1,  # month
                    type=2,  # store
                    income=v['income'],
                    profit=v['profit'],
                    count=v['count'],
                    income_yoy=income_yoy,
                    profit_yoy=profit_yoy,
                    income_mom=income_mom,
                    profit_mom=profit_mom,
                )
                db.session.add(product_master)
            else:
                product_store_month.income = float(
                    product_store_month.income) + v['income']
                product_store_month.profit = float(
                    product_store_month.profit) + v['profit']
                product_store_month.count = float(
                    product_store_month.count) + v['count']

                if product_store_last_year_month != None:
                    # 销售同比
                    product_store_month.income_yoy = round(
                        product_store_month.income / float(
                            product_store_last_year_month.income) * 100, 2)
                    # 利润同比
                    product_store_month.profit_yoy = round(
                        product_store_month.profit / float(
                            product_store_last_year_month.
                            profit) * 100, 2)

                if product_store_last_month != None:
                    # 销售环比
                    product_store_month.income_mom = round(
                        product_store_month.income / float(
                            product_store_last_month.income) * 100, 2)
                    # 利润环比
                    product_store_month.profit_mom = round(
                        product_store_month.profit / float(
                            product_store_last_month.profit) * 100, 2)

    def __refund_master_year(self):
        """订单退款时 主账户下sku 按年销售统计"""
        for v in self.sku_price_count:
            product_master_year = self.__get_product_master(
                v['sku_id'], 2, self.year)
            product_master_last_year = self.__get_product_master(
                v['sku_id'], 2, self.last_year)

            product_master_year.income = float(
                product_master_year.income) - v['income']
            product_master_year.profit = float(
                product_master_year.profit) - v['profit']
            product_master_year.count = float(
                product_master_year.count) - v['count']
            if product_master_last_year != None:
                # 销售同比
                product_master_year.income_yoy = round(
                    product_master_year.income / float(
                        product_master_last_year.income) * 100, 2)
                # 利润同比
                product_master_year.profit_yoy = round(
                    product_master_year.profit / float(
                        product_master_last_year.profit) * 100, 2)

    def __refund_master_month(self):
        """订单退款时  主账户 sku按月销售统计"""
        for v in self.sku_price_count:
            product_master_month = self.__get_product_master(
                v['sku_id'], 1, self.month)
            product_master_last_month = self.__get_product_master(
                v['sku_id'], 1, self.last_month)
            product_master_last_year_month = self.__get_product_master(
                v['sku_id'], 1, self.last_year_month)

            product_master_month.income = float(
                product_master_month.income) - v['income']
            product_master_month.profit = float(
                product_master_month.profit) - v['profit']
            product_master_month.count = float(
                product_master_month.count) - v['count']

            if product_master_last_year_month != None:
                # 销售同比
                product_master_month.income_yoy = round(
                    product_master_month.income / float(
                        product_master_last_year_month.income) * 100, 2)
                # 利润同比
                product_master_month.profit_yoy = round(
                    product_master_month.profit / float(
                        product_master_last_year_month.profit) * 100, 2)

            if product_master_last_month != None:
                # 销售环比
                product_master_month.income_mom = round(
                    product_master_month.income / float(
                        product_master_last_month.income) * 100, 2)
                # 利润环比
                product_master_month.profit_mom = round(
                    product_master_month.profit / float(
                        product_master_last_month.profit) * 100, 2)

    def __refund_store_year(self):
        """订单退款时 下属店铺sku按年销售统计"""
        for v in self.sku_price_count:
            product_store_year = self.__get_product_store(
                v['sku_id'], 2, self.year)
            product_store_last_year = self.__get_product_store(
                v['sku_id'], 2, self.last_year)

            product_store_year.income = float(
                product_store_year.income) - v['income']
            product_store_year.profit = float(
                product_store_year.profit) - v['profit']
            product_store_year.count = float(
                product_store_year.count) - v['count']

            if product_store_last_year != None:
                # 销售同比
                product_store_year.income_yoy = round(
                    product_store_year.income / float(
                        product_store_last_year.income) * 100, 2)
                # 利润同比
                product_store_year.profit_yoy = round(
                    product_store_year.profit / float(
                        product_store_last_year.profit) * 100, 2)

    def __refund_store_month(self):
        """订单退款时 下属店铺sku按月销售统计"""
        for v in self.sku_price_count:
            product_store_month = self.__get_product_store(
                v['sku_id'], 1, self.month)
            product_store_last_month = self.__get_product_store(
                v['sku_id'], 1, self.last_month)
            product_store_last_year_month = self.__get_product_store(
                v['sku_id'], 1, self.last_year_month)

            product_store_month.income = float(
                product_store_month.income) - v['income']
            product_store_month.profit = float(
                product_store_month.profit) - v['profit']
            product_store_month.count = float(
                product_store_month.count) - v['count']

            if product_store_last_year_month != None:
                # 销售同比
                product_store_month.income_yoy = round(
                    product_store_month.income / float(
                        product_store_last_year_month.income) * 100, 2)
                # 利润同比
                product_store_month.profit_yoy = round(
                    product_store_month.profit / float(
                        product_store_last_year_month.
                        profit) * 100, 2)

            if product_store_last_month != None:
                # 销售环比
                product_store_month.income_mom = round(
                    product_store_month.income / float(
                        product_store_last_month.income) * 100, 2)
                # 利润环比
                product_store_month.profit_mom = round(
                    product_store_month.profit / float(
                        product_store_last_month.profit) * 100, 2)

    