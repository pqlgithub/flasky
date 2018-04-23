# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext
from app import db
from ..utils import timestamp
from ..constant import SUPPORT_PLATFORM
from app.models import User

__all__ = [
    'Store',
    'StoreProduct',
    'StoreDistributeProduct',
    'StoreDistributePacket',
    'STORE_STATUS',
    'STORE_TYPE'
]

# 渠道的状态
STORE_STATUS = [
    (1, lazy_gettext('Enabled'), 'success'),
    (-1, lazy_gettext('Disabled'), 'danger')
]

# 渠道的类型
STORE_TYPE = [
    # 小程序
    (3, lazy_gettext('Wx App')),
    # 线下店铺
    (5, lazy_gettext('Offline Store')),
    # 分销商
    (6, lazy_gettext('Distribution')),
    # 第三方电商
    (7, lazy_gettext('Third party E-commerce'))
]


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

    # 类型：3、小程序 5、实体店铺 6、分销 7、第三方店铺；10、自营；
    type = db.Column(db.SmallInteger, default=1)
    # 状态 -1：禁用；1：正常
    status = db.Column(db.SmallInteger, default=1)
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

    @property
    def platform_name(self):
        for plat in SUPPORT_PLATFORM:
            if plat['id'] == self.platform:
                return plat['name']
        return None

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

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'rid': self.serial_no,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'status': self.status
        }
        return json_obj

    def __repr__(self):
        return '<Store %r>' % self.name


class StoreProduct(db.Model):
    """店铺与商品关系表"""

    __tablename__ = 'store_products'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)

    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    # 是否为分销商品
    is_distributed = db.Column(db.Boolean, default=False)
    # 上架 或 下架 状态
    status = db.Column(db.Boolean, default=False)

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'store_id': self.store_id,
            'is_distributed': self.is_distributed,
            'status': self.status
        }
        return json_obj

    def __repr__(self):
        return '<StoreProduct {}>'.format(self.id)


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
