# -*- coding: utf-8 -*-
from flask import current_app
from flask_babelex import gettext, lazy_gettext
from app import db
from ..utils import timestamp
from ..constant import INWAREHOUSE_STATUS, WAREHOUSE_OPERATION_TYPE, DEFAULT_IMAGES, OUTWAREHOUSE_STATUS
from .purchase import Purchase
from .currency import Currency

__all__ = [
    'Warehouse',
    'WarehouseShelve',
    'InWarehouse',
    'OutWarehouse',
    'StockHistory',
    'ExchangeWarehouse',
    'ExchangeWarehouseProduct'
]


WAREHOUSE_TYPES = [
    (1, lazy_gettext('Private Build')),
    (2, lazy_gettext('Leased'))
]

SHELVE_TYPES = [
    (1, gettext('Qualified'), lazy_gettext('Qualified')),
    (2, gettext('Defective'), lazy_gettext('Defective'))
]

class Warehouse(db.Model):
    """仓库"""
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    # 币种
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'))
    name = db.Column(db.String(32), nullable=False)
    address = db.Column(db.String(128))
    en_address = db.Column(db.String(128))
    description = db.Column(db.String(255))
    # 仓库负责人
    username = db.Column(db.String(32), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    email = db.Column(db.String(64), nullable=True)
    qq = db.Column(db.String(32), nullable=True)
    # 类型 1: 自建仓库 2：第三方仓库
    type = db.Column(db.SmallInteger, default=1)
    # 状态 -1： 禁用（默认）1：启用
    status = db.Column(db.SmallInteger, default=1)
    # 是否默认仓库
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def currency_unit(self):
        """当前货币单位"""
        if self.currency_id:
            current_currency = Currency.query.get(self.currency_id)
            return current_currency.code
        else:
            return None

    @property
    def default_shelve(self):
        """返回默认货架"""
        default_shelve = self.shelves.filter_by(is_default=True).first()
        if not default_shelve:
            return self.shelves.first()
        return default_shelve

    # warehouse to shelves => 1 to N
    shelves = db.relationship(
        'WarehouseShelve', backref='warehouse', lazy='dynamic'
    )

    # warehouse to purchase => 1 to N
    purchases = db.relationship(
        'Purchase', backref='warehouse', lazy='dynamic'
    )

    # warehouse to in_warehouse => 1 to N
    in_warehouse = db.relationship(
        'InWarehouse', backref='warehouse', lazy='dynamic'
    )

    # warehouse to out_warehouse => 1 to N
    out_warehouse = db.relationship(
        'OutWarehouse', backref='warehouse', lazy='dynamic'
    )

    # warehouse to stock_history => 1 to N
    stock_history = db.relationship(
        'StockHistory', backref='warehouse', lazy='dynamic'
    )

    # warehouse to stock => 1 to N
    product_stock = db.relationship(
        'ProductStock', backref='warehouse', lazy='dynamic'
    )

    # warehouse to shipper => 1 to 1
    shipper = db.relationship(
        'Shipper', backref='warehouse', uselist=False
    )


    @classmethod
    def wh_types(self):
        return WAREHOUSE_TYPES

    @property
    def desc_type(self):
        for t in WAREHOUSE_TYPES:
            if t[0] == self.type:
                return t

    def __repr__(self):
        return '<Warehouse %r>' % self.name

    def to_json(self):
        """资源和JSON的序列化转换"""
        return {
            c.name: getattr(self, c.name, None) for c in self.__table__.columns
        }


class WarehouseShelve(db.Model):
    """仓库 / 货架"""
    __tablename__ = 'warehouse_shelves'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, nullable=False)
    # 类型 1：良品 2：次品
    type = db.Column(db.SmallInteger, default=1)
    description = db.Column(db.String(255), nullable=True)
    # 默认货架位
    is_default = db.Column(db.Boolean, default=False)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))

    # warehouse shelve to stock_history => 1 to N
    stock_history = db.relationship(
        'StockHistory', backref='warehouse_shelve', lazy='dynamic'
    )

    # warehouse shelve to stock => 1 to N
    product_stock = db.relationship(
        'ProductStock', backref='warehouse_shelve', lazy='dynamic'
    )

    @property
    def type_label(self):
        for type in SHELVE_TYPES:
            if type[0] == self.type:
                return [type[0], type[1]]


    def to_json(self):
        """资源和JSON的序列化转换"""
        json_data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'type_label': self.type_label,
        }
        return json_data

    def __repr__(self):
        return '<Warehouse Shelve %r>' % self.name


class InWarehouse(db.Model):
    """入库单"""

    __tablename__ = 'warehouse_in_list'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    serial_no = db.Column(db.String(20), unique=True, index=True, nullable=False)
    # 关联ID: 采购、订单退货、调拨
    target_serial_no = db.Column(db.String(20), index=True, nullable=False)
    # 类型：1. 采购；2.订单退货；3.调拔
    target_type = db.Column(db.SmallInteger, default=1)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))

    total_quantity = db.Column(db.Integer, default=0)
    # 入库状态： 1、未入库 2、入库中 3、入库完成
    in_status = db.Column(db.SmallInteger, default=1)
    # 入库流程状态
    status = db.Column(db.SmallInteger, default=1)
    remark = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # db.UniqueConstraint
    __table_args__ = (
        db.Index('ix_target_serial_type', 'target_serial_no', 'target_type'),
    )

    @property
    def status_label(self):
        for s in INWAREHOUSE_STATUS:
            if s[0] == self.in_status:
                return s

    @property
    def target(self):
        if self.target_type == 1:
            return Purchase.query.filter_by(serial_no=self.target_serial_no).first()
        return None

    @property
    def target_label(self):
        if self.target_type == 1:
            return lazy_gettext('Purchase')
        return None


    def __repr__(self):
        return '<InWarehouse %r>' % self.serial_no


class OutWarehouse(db.Model):
    """出库单"""

    __tablename__ = 'warehouse_out_list'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    serial_no = db.Column(db.String(20), unique=True, index=True, nullable=False)
    # 关联ID: 订单ID、订单退货、调拨
    target_serial_no = db.Column(db.String(20), index=True, nullable=False)
    # 类型：1. 订单出库；2.订单退货；3.调拔; 10.孤立出库 (target_id=0);
    target_type = db.Column(db.SmallInteger, default=1)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    total_quantity = db.Column(db.Integer, default=0)
    out_quantity = db.Column(db.Integer, default=0)
    # 出库状态： 1、未出库 2、出库中 3、出库完成
    out_status = db.Column(db.SmallInteger, default=1)
    # 出库流程状态
    status = db.Column(db.SmallInteger, default=1)
    remark = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    __table_args__ = (
        db.Index('ix_target_serial_type','target_serial_no', 'target_type'),
    )

    @property
    def status_label(self):
        for s in OUTWAREHOUSE_STATUS:
            if s[0] == self.out_status:
                return s

    @property
    def target_label(self):
        if self.target_type == 1:
            return lazy_gettext('Order')
        return None

    def mark_out_status_finished(self):
        """更新出库状态为已完成"""
        self.out_status = 3


    def __repr__(self):
        return '<OutWarehouse %r>' % self.serial_no


class StockHistory(db.Model):
    """库存变化的历史记录明细"""

    __tablename__ = 'warehouse_stock_history'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    warehouse_shelve_id = db.Column(db.Integer, db.ForeignKey('warehouse_shelves.id'))

    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)

    # 出库单/入库单 编号
    serial_no = db.Column(db.String(20), index=True, nullable=False)
    # 类型：1、入库 2：出库
    type = db.Column(db.SmallInteger, default=1)
    # 操作类型
    operation_type = db.Column(db.SmallInteger, default=1)
    # 原库存数量
    original_quantity = db.Column(db.Integer, default=0)
    # 变化数量
    quantity = db.Column(db.Integer, default=1)
    # 当前数量
    current_quantity = db.Column(db.Integer, default=0)
    # 原价格
    ori_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # in_warehouse and products => 1 to 1
    sku = db.relationship(
        'ProductSku', backref='stock_history', uselist=False
    )

    @property
    def cover(self):
        """获取对应产品的封面图"""
        sku = self.sku
        if not sku:
            return DEFAULT_IMAGES['cover']
        return sku.cover

    @property
    def symbol(self):
        """运算符号"""
        return '+' if self.type == 1 else '-'

    @property
    def operate_type_label(self):
        for s in WAREHOUSE_OPERATION_TYPE:
            if s[0] == self.operation_type:
                return s


    def __repr__(self):
        return '<StockHistory %r>' % self.product_sku_id


class ExchangeWarehouse(db.Model):
    """调拨单"""

    __tablename__ = 'warehouse_exchange_list'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    serial_no = db.Column(db.String(20), unique=True, index=True, nullable=False)
    out_warehouse_id = db.Column(db.Integer, default=0)
    in_warehouse_id = db.Column(db.Integer, default=0)
    total_quantity = db.Column(db.Integer, default=0)
    # 库存状态： 1、未开始（默认）2、调拨中 3、已完成
    out_in_status = db.Column(db.SmallInteger, default=1)
    # 调拨单状态： 1、未审核 2、业务主管 3、批准
    status = db.Column(db.SmallInteger, default=1)
    remark = db.Column(db.String(255), nullable=True)

    is_verified = db.Column(db.Boolean, default=False)
    verified_user_id = db.Column(db.Integer, default=0)
    verified_at = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # exchange and item => 1 to N
    products = db.relationship(
        'ExchangeWarehouseProduct', backref='exchange_warehouse', lazy='dynamic'
    )

    def __repr__(self):
        return '<ExchangeWarehouse %r>' % self.serial_no


class ExchangeWarehouseProduct(db.Model):
    """调拨单产品明细"""

    __tablename__ = 'warehouse_exchange_products'
    id = db.Column(db.Integer, primary_key=True)
    exchange_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_exchange_list.id'))
    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    total_quantity = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint('exchange_warehouse_id', 'product_sku_id', name='uix_ex_warehouse_sku_id'),
    )

    def __repr__(self):
        return '<ExchangeWarehouseProduct %r>' % self.id
