# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext
from app import db
from ..utils import timestamp
from ..constant import SUPPORT_PLATFORM
from app.models import User

__all__ = [
    'Store',
    'StoreDistributeProduct',
    'StoreDistributePacket',
    'STORE_STATUS',
    'STORE_TYPE',
    'STORE_MODES'
]

# 渠道的状态
STORE_STATUS = [
    (1, lazy_gettext('Enabled'), 'success'),
    (-1, lazy_gettext('Disabled'), 'danger')
]

# 选品模式
STORE_MODES = [
    (1, lazy_gettext('ALL Mode')),
    (2, lazy_gettext('Distribute Mode'))
]

# 渠道的类型
STORE_TYPE = [
    # 第三方电商
    (1, lazy_gettext('Authorized Store')),
    # 自营电商
    (2, lazy_gettext('B2C E-commerce')),
    # 社交电商，如：小程序
    (3, lazy_gettext('Social E-commerce')),
    # 线下店铺
    (5, lazy_gettext('Offline Store')),
    # 分销商
    (6, lazy_gettext('Distribution'))
]

# store and product => N to N
store_product_table = db.Table('stores_products',
                               db.Column('store_id', db.Integer, db.ForeignKey('stores.id')),
                               db.Column('product_id', db.Integer, db.ForeignKey('products.id')))


class Store(db.Model):
    """渠道店铺列表"""
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    # 负责人
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    name = db.Column(db.String(30), index=True)
    serial_no = db.Column(db.String(10), unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)
    
    # 授权平台
    platform = db.Column(db.Integer, default=0)
    # 授权过期时间
    authorize_expired_at = db.Column(db.Integer, default=0)
    access_token = db.Column(db.String(100), default='')
    refresh_token = db.Column(db.String(100), default='')

    # 类型：1、第三方店铺；2、自营；3、社交电商 5、实体店铺 6、分销
    type = db.Column(db.SmallInteger, default=1)
    # 状态 -1：禁用；1：正常
    status = db.Column(db.SmallInteger, default=1)
    # 选品模式 1: 全品； 2：授权部分商品
    distribute_mode = db.Column(db.SmallInteger, default=1)
    # 是否设置私有库存
    is_private_stock = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # store and account => 1 to N
    accounts = db.relationship(
        'PayAccount', backref='store', lazy='dynamic'
    )

    # store and orders => 1 to N
    orders = db.relationship(
        'Order', backref='store', lazy='dynamic'
    )

    # store and store_statistics => 1 to N
    store_statistics = db.relationship(
        'StoreStatistics', backref='store', lazy='dynamic'
    )

    # store and product_packet => 1 to N
    distribute_packets = db.relationship(
        'StoreDistributePacket', backref='store', lazy='dynamic'
    )

    # store and product => N to N
    products = db.relationship(
        'Product', secondary=store_product_table, backref=db.backref('stores', lazy='select'), lazy='dynamic'
    )

    @property
    def platform_name(self):
        for plat in SUPPORT_PLATFORM:
            if plat['id'] == self.platform:
                return plat['name']
        return None

    @property
    def mode_label(self):
        for m in STORE_MODES:
            if m[0] == self.distribute_mode:
                return m

    @property
    def status_label(self):
        for s in STORE_STATUS:
            if s[0] == self.status:
                return s
            
    @property
    def type_label(self):
        for t in STORE_TYPE:
            if t[0] == self.type:
                return t
    
    @property
    def operator(self):
        """获取负责人信息"""
        return User.query.get(self.operator_id) if self.operator_id else None

    @property
    def wxapp(self):
        """关联小程序信息"""
        from .weixin import WxMiniApp
        if self.platform == 1:
            return WxMiniApp.query.filter_by(serial_no=self.serial_no).first()

    @staticmethod
    def validate_unique_name(name, master_uid, platform):
        """验证店铺名称是否唯一"""
        return Store.query.filter_by(master_uid=master_uid, platform=platform, name=name).first()

    def add_product(self, *products):
        """添加商品"""
        self.products.extend([product for product in products if product not in self.products])

    def update_product(self, *products):
        """更新商品"""
        self.products = [product for product in products]

    def remove_product(self, *products):
        """删除商品"""
        self.products = [product for product in self.products if product not in products]

    def __repr__(self):
        return '<Store %r>' % self.name


class StoreDistributeProduct(db.Model):
    """店铺授权或分销商品扩展信息"""

    __tablename__ = 'store_product_extend'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_serial_no = db.Column(db.String(12), index=True, nullable=False)

    sku_id = db.Column(db.Integer, default=0)
    sku_serial_no = db.Column(db.String(12), index=True, nullable=True)

    # 零售价
    price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 促销价
    sale_price = db.Column(db.Numeric(precision=10, scale=2), default=0)

    # 私有库存数
    private_stock = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<StoreDistributeProduct {}>'.format(self.store_id)


class StoreDistributePacket(db.Model):
    """店铺与商品组关系表"""

    __tablename__ = 'store_distribute_packets'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)

    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    product_packet_id = db.Column(db.Integer, db.ForeignKey('product_packets.id'))
    discount_templet_id = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<StoreDistributePacket {}>'.format(self.id)
