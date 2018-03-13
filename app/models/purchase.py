# -*- coding: utf-8 -*-
from sqlalchemy import text, event
from jieba.analyse.analyzer import ChineseAnalyzer
from app import db
from ..utils import timestamp, gen_serial_no
from ..constant import PURCHASE_STATUS, PURCHASE_PAYED, DEFAULT_IMAGES

__all__ = [
    'Purchase',
    'PurchaseProduct',
    'PurchaseReturned',
    'PurchaseReturnedProduct'
]


class Purchase(db.Model):
    """采购单"""

    __tablename__ = 'purchases'

    __searchable__ = ['serial_no', 'express_no', 'product_name', 'product_sku', 'supplier_name']
    __analyzer__ = ChineseAnalyzer()

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    serial_no = db.Column(db.String(16), unique=True, index=True, nullable=False)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    # sku种类
    sku_count = db.Column(db.Integer, default=0)
    quantity_sum = db.Column(db.Integer, default=0)
    in_quantity = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)
    # 运费
    freight = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)
    # 其他费用（附加费用）
    extra_charge = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)

    # express info
    express_name = db.Column(db.String(30), nullable=True)
    express_no = db.Column(db.String(255), nullable=True)

    # 预计到货时间
    arrival_date = db.Column(db.Date, nullable=True)
    # 实际到货时间
    arrival_at = db.Column(db.Integer, default=0)
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

    @property
    def first_child(self):
        """默认采购产品的第一个的封面图"""
        return self.products.first()

    @property
    def cover(self):
        """获取采购的第一个商品的封面图"""
        if not self.first_child:
            return DEFAULT_IMAGES['cover']
        sku = self.first_child.sku
        if not sku:
            return DEFAULT_IMAGES['cover']
        return sku.cover

    @property
    def product_name(self):
        """返回采购产品的名称"""
        product_name = []
        for item in self.products:
            sku = item.sku
            if sku and sku.product:
                product_name.append(sku.product.name)
        return ';'.join(product_name)

    @property
    def product_sku(self):
        """返回采购SKU"""
        product_sku = []
        for item in self.products:
            product_sku.append(item.sku_serial_no)
        return ';'.join(product_sku)

    @property
    def supplier_name(self):
        current_supplier = self.supplier
        return '{} {}'.format(current_supplier.short_name, current_supplier.full_name)

    @property
    def payable_amount(self):
        """应支付的金额"""
        return self.total_amount + self.freight + self.extra_charge

    def validate_finished(self, new_quantity=0):
        """检测是否入库完成"""
        return True if self.quantity_sum - self.in_quantity == new_quantity else False

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
        if Purchase.query.filter_by(serial_no=serial_no).first() is None:
            return serial_no
        while True:
            new_serial_no = gen_serial_no()
            if Purchase.query.filter_by(serial_no=new_serial_no).first() is None:
                break
        return new_serial_no

    @staticmethod
    def on_sync_change(mapper, connection, target):
        """同步数据事件"""
        from app.tasks import sync_supply_stats

        if target.supplier_id:
            sync_supply_stats.apply_async(args=[target.master_uid, target.supplier_id])

    def to_json(self):
        """资源和JSON的序列化转换"""
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    def __repr__(self):
        return '<Purchase %r>' % self.serial_no


class PurchaseProduct(db.Model):
    """采购单商品明细"""

    _tablename__ = 'purchase_products'
    id = db.Column(db.Integer, primary_key=True)
    # 采购单
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'))

    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)

    cost_price = db.Column(db.Numeric(precision=10, scale=2), default=0.0000)
    quantity = db.Column(db.Integer, default=0)
    in_quantity = db.Column(db.Integer, default=0)
    tax_rate = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    freight = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    __table_args__ = (
        db.UniqueConstraint('purchase_id', 'product_sku_id', name='uix_purchase_sku_id'),
    )

    # purchase and products => 1 to 1
    sku = db.relationship(
        'ProductSku', backref='purchase_product', uselist=False
    )

    @property
    def cover(self):
        """获取商品的封面图"""
        sku = self.sku
        if not sku:
            return DEFAULT_IMAGES['cover']
        return sku.cover

    @property
    def is_finished(self):
        """是否完成入库"""
        return True if self.quantity == self.in_quantity else False

    def validate_quantity(self, offset_quantity):
        """验证数量是否匹配"""
        return True if self.quantity - self.in_quantity >= offset_quantity else False

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

    __table_args__ = (
        db.UniqueConstraint('purchase_returned_id', 'product_sku_id', name='uix_purchase_sku_id'),
    )

    def __repr__(self):
        return '<PurchaseReturnedProduct %r>' % self.id


# 添加监听事件, 实现触发器
event.listen(Purchase, 'after_insert', Purchase.on_sync_change)
