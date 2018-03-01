# -*- coding: utf-8 -*-
from flask import abort, g, current_app
from sqlalchemy import text, event
from flask_babelex import lazy_gettext, gettext
from jieba.analyse.analyzer import ChineseAnalyzer
import flask_whooshalchemyplus
from app import db
from .product import ProductSku
from .logistics import Express
from ..utils import timestamp
from app.helpers import MixGenId

__all__ = [
    'Order',
    'OrderItem',
    'OrderStatus',
    'Cart'
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
    # 配货中
    DISTRIBUTION = 12
    # 待打印
    PENDING_PRINT = 13
    # 已发货
    SHIPPED = 16
    # 待签收
    PENDING_SIGNED = 17
    # 已签收
    SIGNED = 20
    # 订单完成
    FINISHED = 30
    # 待评分
    PENDING_RATING = 40
    # 评分完成
    RATED = 45
    # 已退款
    REFUND = 90


# 订单状态
ORDER_STATUS = [
    (OrderStatus.CANCELED, lazy_gettext('Canceled'), 'info'),
    (OrderStatus.PENDING_PAYMENT, gettext('Pending Payment'), 'danger'),
    (OrderStatus.PENDING_CHECK, lazy_gettext('UnApprove'), 'danger'),
    (OrderStatus.PENDING_SHIPMENT, lazy_gettext('Effective'), 'primary'),
    (OrderStatus.DISTRIBUTION, lazy_gettext('Distribution'), 'primary'),
    (OrderStatus.PENDING_PRINT, lazy_gettext('UnPrinting'), 'primary'),
    (OrderStatus.SHIPPED, lazy_gettext('Shipped'), 'warning'),
    (OrderStatus.PENDING_SIGNED, lazy_gettext('Pending Signed'), 'warning'),
    (OrderStatus.SIGNED, lazy_gettext('Signed'), 'success'),
    (OrderStatus.REFUND, lazy_gettext('Refund'), 'warning'),
    (OrderStatus.FINISHED, lazy_gettext('Pending Finished'), 'success'),
    (OrderStatus.PENDING_RATING, lazy_gettext('Pending Rating'), 'success'),
    (OrderStatus.RATED, lazy_gettext('Rated'), 'success')
]


class Order(db.Model):
    """订单表"""

    __tablename__ = 'orders'

    __searchable__ = ['serial_no', 'outside_target_id', 'express_no', 'buyer_name', 'buyer_tel', 'buyer_phone', 'all_items']
    __analyzer__ = ChineseAnalyzer()

    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.String(20), unique=True, index=True, nullable=False)

    # 用户ID
    master_uid = db.Column(db.Integer, index=True, default=0)
    # 消费者ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 第三方平台订单编号
    outside_target_id = db.Column(db.String(32), index=True, nullable=True)
    # 店铺ID
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    
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
    express_id = db.Column(db.Integer, default=0)
    # 运单号
    express_no = db.Column(db.String(32), nullable=True)
    # 卖家备注
    remark = db.Column(db.String(255), nullable=True)
    # 发票类型： 1、不需要发票 2、电子发票 3、纸质发票
    invoice_type = db.Column(db.SmallInteger, default=1)

    # 顾客信息
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    buyer_name = db.Column(db.String(50), index=True, nullable=False)
    buyer_tel = db.Column(db.String(20), index=True, nullable=True)
    buyer_phone = db.Column(db.String(20), index=True, nullable=True)
    buyer_zipcode = db.Column(db.String(16), nullable=True)
    buyer_address = db.Column(db.String(200), nullable=True)
    buyer_country = db.Column(db.String(50), nullable=True)
    buyer_province = db.Column(db.String(50), nullable=True)
    buyer_city = db.Column(db.String(50), nullable=True)
    buyer_town = db.Column(db.String(50), nullable=True)
    buyer_area = db.Column(db.String(50), nullable=True)
    # 买家备注
    buyer_remark = db.Column(db.String(250), nullable=True)
    # 订单状态
    status = db.Column(db.SmallInteger, default=OrderStatus.PENDING_PAYMENT)
    # 是否挂起
    suspend = db.Column(db.Boolean, default=False)
    # 过期时间
    expired_time = db.Column(db.Integer, nullable=True)
    
    # 分销商ID
    customer_id = db.Column(db.String(20), nullable=True)
    # 所属销售人员
    saler_uid = db.Column(db.Integer, default=0)
    # 来源终端, 1、WX 2、H5 3、App 4、TV 5、POS 6、PAD
    from_client = db.Column(db.SmallInteger, default=0)
    # 推广码
    affiliate_code = db.Column(db.String(16), nullable=True)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    # 审单人
    verified_uid = db.Column(db.Integer, default=0)
    # 审核时间
    verified_at = db.Column(db.Integer, default=0)
    # 支付时间
    payed_at = db.Column(db.Integer, default=0)
    # 发货时间
    express_at = db.Column(db.Integer, default=0)
    # 发货人
    deliver_uid = db.Column(db.Integer, default=0)
    # 收货时间
    received_at = db.Column(db.Integer, default=0)
    # 完成时间
    finished_at = db.Column(db.Integer, default=0)
    # 关闭或取消时间
    closed_at = db.Column(db.Integer, default=0)
    # 订单类型 1、正常订单；2、拆分子订单;7、售后订单；
    type = db.Column(db.SmallInteger, default=1)
    # 相关订单
    related_rid = db.Column(db.String(20), nullable=True)
    # 售后客服
    service_uid = db.Column(db.Integer, default=0)
    
    # order and items => 1 to N
    items = db.relationship(
        'OrderItem', backref='order', lazy='dynamic'
    )

    # order and invoice => 1 to 1
    invoice = db.relationship(
        'Invoice', backref='order', uselist=False
    )

    @property
    def rid(self):
        """订单编号别名"""
        return self.serial_no

    @property
    def express(self):
        """关联物流方式"""
        if self.express_id:
            return Express.query.get(self.express_id)
        return None

    @property
    def status_label(self):
        """显示状态标签"""
        for s in ORDER_STATUS:
            if s[0] == self.status:
                return s
        return None

    @property
    def cover(self):
        """默认采购产品的第一个的封面图"""
        sku_id = self.items.first().sku_id
        item_sku = ProductSku.query.get(sku_id)
        return item_sku.cover.view_url

    @property
    def items_count(self):
        """返回明细的数量"""
        return self.items.count()

    @property
    def all_items(self):
        """全部订单明细"""
        sku_list = [item.sku_serial_no for item in self.items]
        return ' '.join(sku_list)

    def mark_checked_status(self):
        """标记为待审核状态"""
        self.status = OrderStatus.PENDING_CHECK

    def mark_shipment_status(self):
        """标记为待发货状态"""
        self.verified_at = timestamp()
        self.status = OrderStatus.PENDING_SHIPMENT

    def mark_print_status(self):
        """标记为待打印状态"""
        self.status = OrderStatus.PENDING_PRINT
        self.express_at = timestamp()

    def mark_shipped_status(self):
        """标记为已发货状态"""
        self.status = OrderStatus.SHIPPED

    def mark_finished_status(self):
        """标记为已完成的状态"""
        self.status = OrderStatus.FINISHED

    def mark_canceled_status(self):
        """标记为关闭或取消状态"""
        self.status = OrderStatus.CANCELED
        self.closed_at = timestamp()

    @staticmethod
    def make_unique_serial_no():
        serial_no = MixGenId.gen_order_sn()
        if Order.query.filter_by(serial_no=serial_no).first() is None:
            return serial_no
        while True:
            new_serial_no = MixGenId.gen_order_sn()
            if Order.query.filter_by(serial_no=new_serial_no).first() is None:
                break
        return new_serial_no

    @staticmethod
    def on_sync_change(mapper, connection, target):
        """同步事件"""
        pass

    @staticmethod
    def create(data, user=None):
        """创建新订单"""
        order = Order(user=user or g.current_user)
        order.from_json(data, partial_update=True)
        
        return order

    def from_json(self, data, partial_update=True):
        """从请求json里导入数据"""
        fields = ['master_uid', 'user_id', 'serial_no', 'store_id', 'outside_target_id',
                  'pay_amount', 'total_amount', 'freight', 'discount_amount', 'invoice_type', 'total_quantity',
                  'buyer_name', 'buyer_tel', 'buyer_phone', 'buyer_zipcode', 'buyer_country', 'buyer_province',
                  'buyer_city', 'buyer_town', 'buyer_area', 'buyer_address', 'buyer_remark',
                  'from_client', 'affiliate_code']
        
        for field in fields:
            try:
                setattr(self, field, data[field])
            except KeyError as err:
                current_app.logger.warn(str(err))
                if not partial_update:
                    abort(400)

    def to_json(self):
        """资源和JSON的序列化转换"""
        opened_columns = ['rid', 'outside_target_id', 'pay_amount', 'total_amount', 'total_quantity', 'freight',
                          'discount_amount', 'express_no', 'remark', 'buyer_name', 'buyer_tel', 'buyer_phone',
                          'buyer_zipcode', 'buyer_address', 'buyer_country', 'buyer_province', 'buyer_city',
                          'buyer_remark', 'created_at', 'express_at', 'received_at', 'status']
        
        json_order = { c: getattr(self, c, None) for c in opened_columns }
        
        # 订单编号
        json_order['outside_target_id'] = self.outside_target_id if self.outside_target_id else self.serial_no
        # 添加快递公司
        json_order['express_name'] = self.express.name if self.express else ''
        # 添加店铺名称
        json_order['store_name'] = '{}({})'.format(self.store.name, self.store.platform_name)
        
        # 添加订单明细
        json_order['items'] = [item.to_json() for item in self.items]
        
        return json_order

    def __repr__(self):
        return '<Order %r>' % self.serial_no


class OrderItem(db.Model):
    """订单明细表"""

    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    # 用户ID
    master_uid = db.Column(db.Integer, index=True, default=0)
    # 仓库ID
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    order_serial_no = db.Column(db.String(20), index=True, nullable=False)
    sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)
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
    
    @property
    def sku(self):
        return ProductSku.query.get(self.sku_id)
    
    def to_json(self):
        """资源和JSON的序列化转换"""
        json_item = {
            'rid': self.sku_serial_no,
            'quantity': self.quantity,
            'deal_price': self.deal_price,
            'discount_amount': self.discount_amount
        }
        return dict(json_item, **self.sku.to_json())

    def __repr__(self):
        return '<OrderItem %r>' % self.id


class Cart(db.Model):
    """购物车"""
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    
    # session id
    sess_id = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, default=0)
    
    api_id = db.Column(db.Integer, default=0)
    recurring_id = db.Column(db.Integer, default=0)
    
    sku_rid = db.Column(db.String(12))
    option = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def product(self):
        return ProductSku.query.filter_by(serial_no=self.sku_rid).first()
    
    def to_json(self):
        """资源和JSON的序列化转换"""
        json_cart = {
            'rid': self.sku_rid,
            'user_id': self.user_id,
            'quantity': self.quantity,
            'option': self.option,
            'product': self.product.to_json() if self.product else {}
        }
        return json_cart

    def __repr__(self):
        return '<Cart {}>'.format(self.id)


# 添加监听事件, 实现触发器
# sqlalchemy.exc.InvalidRequestError: Session is already flushing
# event.listen(Order, 'after_insert', Order.on_sync_change)
