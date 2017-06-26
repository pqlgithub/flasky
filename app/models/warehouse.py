# -*- coding: utf-8 -*-
from flask import current_app

from app import db
from ..utils import timestamp

__all__ = [
    'Warehouse',
    'WarehouseShelve',
    'InWarehouse',
    'InWarehouseProduct',
    'OutWarehouse',
    'OutWarehouseProduct',
    'ExchangeWarehouse',
    'ExchangeWarehouseProduct'
]


WAREHOUSE_TYPES = [
    (1, 'Private'),
    (2, 'Leased')
]

class Warehouse(db.Model):
    """仓库"""
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
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
    # 状态 1： 禁用（默认）2：启用
    status = db.Column(db.SmallInteger, default=1)
    # 是否默认仓库
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # warehouse to shelves => 1 to N
    shelves = db.relationship(
        'WarehouseShelve', backref='warehouse', lazy='dynamic'
    )

    # warehouse to purchase => 1 to N
    purchases = db.relationship(
        'Purchase', backref='warehouse', lazy='dynamic'
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


class WarehouseShelve(db.Model):
    """仓库 / 货架"""
    __tablename__ = 'warehouse_shelves'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    # 类型 1：良品 2：次品
    type = db.Column(db.SmallInteger, default=1)
    description = db.Column(db.String(255), nullable=True)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_data = {
            'id': self.id,
            'name': self.name,
            'type': self.type
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
    target_id = db.Column(db.Integer, default=0)
    # 类型：1. 采购；2.订单退货；3.调拔
    target_type = db.Column(db.SmallInteger, default=1)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    total_quantity = db.Column(db.Integer, default=0)
    in_quantity = db.Column(db.Integer, default=0)
    # 入库状态： 1、未入库 2、入库中 3、入库完成
    in_status = db.Column(db.SmallInteger, default=1)
    # 入库流程状态
    status = db.Column(db.SmallInteger, default=1)
    remark = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # in and item => 1 to N
    products = db.relationship(
        'InWarehouseProduct', backref='in_warehouse', lazy='dynamic'
    )

    def __repr__(self):
        return '<InWarehouse %r>' % self.serial_no



class InWarehouseProduct(db.Model):
    """入库单产品明细"""

    __tablename__ = 'warehouse_in_products'
    id = db.Column(db.Integer, primary_key=True)
    in_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_in_list.id'))
    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    total_quantity = db.Column(db.Integer, default=0)
    in_quantity = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<InWarehouseProduct %r>' % self.product_sku_id


class OutWarehouse(db.Model):
    """出库单"""

    __tablename__ = 'warehouse_out_list'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    serial_no = db.Column(db.String(20), unique=True, index=True, nullable=False)
    # 关联ID: 采购、订单退货、调拨
    target_id = db.Column(db.Integer, default=0)
    # 类型：1. 采购；2.订单退货；3.调拔
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

    # out and item => 1 to N
    products = db.relationship(
        'OutWarehouseProduct', backref='out_warehouse', lazy='dynamic'
    )

    def __repr__(self):
        return '<OutWarehouse %r>' % self.serial_no


class OutWarehouseProduct(db.Model):
    """出库单产品明细"""

    __tablename__ = 'warehouse_out_products'
    id = db.Column(db.Integer, primary_key=True)
    out_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_out_list.id'))
    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    total_quantity = db.Column(db.Integer, default=0)
    out_quantity = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<OutWarehouseProduct %r>' % self.product_sku_id


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

    def __repr__(self):
        return '<ExchangeWarehouseProduct %r>' % self.id
