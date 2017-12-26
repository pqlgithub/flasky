# -*- coding: utf-8 -*-
from app import db

__all__ = ['MasterStatistics', 'StoreStatistics', 'ProductStatistics', 'SalesLogStatistics', 'DaySkuStatistics']


class SalesLogStatistics(db.Model):
    """销售明细统计数据表"""

    __tablename__ = 'sales_log_statistics'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), index=True, nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), index=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    cost_price = db.Column(db.Float, default=0.00)
    deal_price = db.Column(db.Float, default=0.00)
    quantity = db.Column(db.Integer, default=1)
    discount_amount = db.Column(db.Float, default=0.0)
    create_at = db.Column(db.Integer, index=True)
    status = db.Column(db.SmallInteger, default=1)

    def __repr__(self):
        return '<SalesLogStatistics %r>' % self.id


class DaySkuStatistics(db.Model):
    """sku 每天统计数据"""

    __tablename__ = 'day_sku_statistics'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), index=True, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), index=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'), index=True)
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), index=True)
    income = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    profit = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    time = db.Column(db.Integer, index=True)

    __table_args__ = (db.UniqueConstraint('store_id','sku_id','time'), ) 

    def __repr__(self):
        return '<DaySkuStatistics %r>' % self.id


class MasterStatistics(db.Model):
    """ 公司销售统计表 """
    __tablename__ = 'master_statistics'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, nullable=False)
    income = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    profit = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    type = db.Column(db.SmallInteger, nullable=False)
    time = db.Column(db.String(8), nullable=False)
    income_yoy = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    income_mom = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    profit_yoy = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    profit_mom = db.Column(db.Numeric(precision=10, scale=2), nullable=True)

    __table_args__ = (db.Index('master_uid', 'time'), db.UniqueConstraint('master_uid', 'type', 'time'))

    def __repr__(self):
        return '<MasterStatistics %r>' % self.id


class StoreStatistics(db.Model):
    """ 店铺销售统计表 """
    __tablename__ = 'store_statistics'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, nullable=False)
    store_id = db.Column(
        db.Integer, db.ForeignKey('stores.id'), index=True, nullable=False)
    income = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    profit = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    type = db.Column(db.SmallInteger, nullable=False)
    time = db.Column(db.String(8), nullable=False)
    income_yoy = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    income_mom = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    profit_yoy = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    profit_mom = db.Column(db.Numeric(precision=10, scale=2), nullable=True)

    __table_args__ = (db.Index('master_uid', 'time', 'store_id'), db.UniqueConstraint('store_id','type','time'),)

    def __repr__(self):
        return '<StoreStatistics %r>' % self.id


class ProductStatistics(db.Model):
    """商品销售相关统计"""
    # 表名
    __tablename__ = 'product_statistics'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), index=True, nullable=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    income = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    profit = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    time = db.Column(db.String(8), nullable=False)
    # 时间类型 1：月；2：年
    time_type = db.Column(db.SmallInteger, nullable=False)
    # 统计类型 1：主账号；2.下属店铺
    type = db.Column(db.SmallInteger, nullable=False)
    income_yoy = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    income_mom = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    profit_yoy = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    profit_mom = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    count = db.Column(db.Integer,nullable=False)
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)

    __table_args__ = (db.Index(None,'master_uid', 'sku_id','time', 'store_id'), db.UniqueConstraint('store_id', 'sku_id','time','time_type'), )

    def __repr__(self):
        return '<ProductStatistics %r>' % self.id