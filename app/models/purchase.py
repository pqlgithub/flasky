# -*- coding: utf-8 -*-

from app import db
from ..utils import timestamp, gen_serial_no
from ..constant import PURCHASE_STATUS, PURCHASE_PAYED

__all__ = [
    'Purchase',
    'PurchaseProduct',
    'PurchaseReturned',
    'PurchaseReturnedProduct'
]

class Purchase(db.Model):
    """采购单"""

    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    serial_no = db.Column(db.String(16), unique=True, index=True, nullable=False)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    # sku种类
    sku_count = db.Column(db.Integer, default=0)
    quantity_sum = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)
    # 运费
    freight = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)
    # 其他费用（附加费用）
    extra_charge = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)

    # 预计到货时间
    arrival_date = db.Column(db.Date)
    description = db.Column(db.String(255))
    # 状态
    status = db.Column(db.Integer, default=1)
    # 支付阶段
    payed = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # purchase and products => 1 to N
    products = db.relationship(
        'PurchaseProduct', backref='purchase', lazy='dynamic', cascade='delete'
    )


    def update_status(self, status):
        """更新采购单状态"""
        if status in [s[0] for s in PURCHASE_STATUS]:
            self.status = status


    def update_payed(self, paying):
        """更新付款状态"""
        if paying in [p[0] for p in PURCHASE_PAYED]:
            self.payed = paying


    @property
    def status_label(self):
        for status in PURCHASE_STATUS:
            if status[0] == self.status:
                return status

    @property
    def payed_label(self):
        for payed in PURCHASE_PAYED:
            if payed[0] == self.payed:
                return payed

    @staticmethod
    def make_unique_serial_no(serial_no):
        if Purchase.query.filter_by(serial_no=serial_no).first() == None:
            return serial_no
        while True:
            new_serial_no = gen_serial_no()
            if Purchase.query.filter_by(serial_no=new_serial_no).first() == None:
                break
        return new_serial_no

    def __repr__(self):
        return '<Purchase %r>' % self.serial_no


class PurchaseProduct(db.Model):
    """采购单商品明细"""

    _tablename__ = 'purchase_products'
    id = db.Column(db.Integer, primary_key=True)
    # 采购单
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'))

    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    cost_price = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)
    quantity = db.Column(db.Integer, default=0)
    in_quantity = db.Column(db.Integer, default=0)
    tax_rate = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    freight = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # purchase and products => 1 to 1
    sku = db.relationship(
        'ProductSku', backref='purchase_product', uselist=False
    )

    def __repr__(self):
        return '<PurchaseProduct %r>' % self.id


class PurchaseReturned(db.Model):
    """采购退货单"""

    __tablename__ = 'purchase_returned'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    serial_no = db.Column(db.String(20), unique=True, index=True, nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'))
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    total_quantity = db.Column(db.Integer, default=0)
    outed_quantity = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 审核
    is_verified = db.Column(db.Boolean, default=False)
    verified_user_id = db.Column(db.Integer, default=0)
    # 出库状态：1、未出库 2、出库中 3、已出库
    outed_status = db.Column(db.SmallInteger, default=1)
    # 退货单流程状态
    status = db.Column(db.SmallInteger, default=1)
    remark = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<PurchaseReturned %r>' % self.id


class PurchaseReturnedProduct(db.Model):
    """采购退货单商品明细"""

    __tablename__ = 'purchase_returned_products'
    id = db.Column(db.Integer, primary_key=True)
    purchase_returned_id = db.Column(db.Integer, db.ForeignKey('purchase_returned.id'))
    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    returned_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    returned_quantity = db.Column(db.Integer, default=0)
    outed_quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<PurchaseReturnedProduct %r>' % self.id