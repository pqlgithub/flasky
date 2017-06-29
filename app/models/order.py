# -*- coding: utf-8 -*-
from flask_babelex import gettext
from app import db
from ..utils import timestamp

__all__ = [
    'Order',
    'OrderItem',
    'OrderStatus'
]

# 发票类型
INVOICE_TYPE = [
    (1, '不要发票'),
    (2, '电子发票'),
    (3, '纸质发票')
]

class OrderStatus:
    # 已关闭或取消
    CANCELED = -1
    # 待支付
    PENDING_PAYMENT = 1
    # 待审核
    PENDING_CHECK = 5
    # 待发货
    PENDING_SHIPMENT = 10
    # 已发货
    SHIPPED = 15
    # 订单完成
    FINISHED = 20
    # 待评分
    PENDING_RATING = 25
    # 评分完成
    RATED = 30


class Order(db.Model):
    """订单表"""

    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.Integer, unique=True, index=True, nullable=False)

    # 用户ID
    master_uid = db.Column(db.Integer, index=True, default=0)
    # 第三方平台订单编号
    outside_target_id = db.Column(db.String(32), index=True, nullable=True)
    # 店铺ID
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    # 仓库ID
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    # 支付金额
    pay_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 总金额
    total_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 总数量
    total_quantity = db.Column(db.Integer, default=0)
    # 运费
    freight = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 优惠金额
    discount_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 物流ID
    express_id = db.Column(db.Integer, db.ForeignKey('expresses.id'))
    # 运单号
    express_no = db.Column(db.String(32), nullable=True)
    # 卖家备注
    remark = db.Column(db.String(255), nullable=True)
    # 发票类型： 1、不需要发票 2、电子发票 3、纸质发票
    invoice_type = db.Column(db.SmallInteger, default=1)

    # 顾客信息
    buyer_name = db.Column(db.String(50), index=True, nullable=False)
    buyer_tel = db.Column(db.String(20), index=True, nullable=True)
    buyer_phone = db.Column(db.String(20), index=True, nullable=True)
    buyer_zipcode = db.Column(db.String(16), nullable=True)
    buyer_address = db.Column(db.String(200), nullable=True)
    buyer_country = db.Column(db.String(50), nullable=True)
    buyer_province = db.Column(db.String(50), nullable=True)
    buyer_city = db.Column(db.String(50), nullable=True)
    # 买家备注
    buyer_remark = db.Column(db.String(250), nullable=True)
    # 订单状态
    status = db.Column(db.SmallInteger, default=OrderStatus.PENDING_PAYMENT)
    # 是否挂起
    suspend = db.Column(db.Boolean, default=False)
    # 过期时间
    expired_time = db.Column(db.Integer, nullable=True)
    # 来源终端
    from_client = db.Column(db.SmallInteger, default=0)
    # 推广码
    affiliate_code = db.Column(db.String(16), nullable=True)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    # 审核时间
    verified_at = db.Column(db.Integer, default=0)
    # 支付时间
    payed_at = db.Column(db.Integer, default=0)
    # 关闭或取消时间
    closed_at = db.Column(db.Integer, default=0)

    # order and items => 1 to N
    items = db.relationship(
        'OrderItem', backref='order', lazy='dynamic'
    )

    # order and invoice => 1 to 1
    invoice = db.relationship(
        'Invoice', backref='order', uselist=False
    )

    def __repr__(self):
        return '<Order %r>' % self.serial_no


class OrderItem(db.Model):
    """订单明细表"""

    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    sku_serial_no = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    # 交易价格
    deal_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 优惠金额
    discount_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 1：默认
    type = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    __table_args__ = (
        db.UniqueConstraint('order_id', 'sku_id', name='uix_order_id_sku_id'),
    )

    def __repr__(self):
        return '<OrderItem %r>' % self.id








