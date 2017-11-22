# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext
from app import db
from ..utils import timestamp

__all__ = [
    'AppService',
    'SubscribeService',
    'SubscribeRecord'
]

# 产品的状态
STORE_STATUS = [
    (1, lazy_gettext('Enabled'), 'success'),
    (-1, lazy_gettext('Disabled'), 'danger')
]

class AppService(db.Model):
    """应用市场"""
    
    __tablename__ = 'app_services'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.String(10), unique=True, index=True)
    
    name = db.Column(db.String(30), index=True)
    # app icon
    icon_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    # 服务摘要(亮点)
    summary = db.Column(db.String(140), nullable=False)
    # 服务介绍
    description = db.Column(db.String(255), nullable=True)
    # 备注事项
    remark = db.Column(db.String(255), nullable=True)
    # 应用类型：营销插件、渠道应用、供销管理、主题皮肤
    type = db.Column(db.SmallInteger, default=1)
    # 是否免费
    is_free= db.Column(db.Boolean, default=True)
    # 收费价格
    sale_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 月付费/包年费则优惠2个月
    pay_mode = db.Column(db.SmallInteger, default=1)
    
    # 购买次数
    sale_count = db.Column(db.Integer, default=0)
    
    # 状态 -1：禁用；1：待审核； 2：已上架
    status = db.Column(db.SmallInteger, default=1)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    

    def __repr__(self):
        return '<AppService %r>' % self.name
    

class SubscribeService(db.Model):
    """已订购的服务"""

    __tablename__ = 'subscribe_services'

    id = db.Column(db.Integer, primary_key=True)

    master_uid = db.Column(db.Integer, default=0)
    service_id = db.Column(db.Integer, db.ForeignKey('app_services.id'))

    # 订购时间
    ordered_at = db.Column(db.Integer, default=timestamp)
    # 过期时间,-1为永久不过期
    expired_at = db.Column(db.Integer, default=-1)
    # 状态 -1：未过期；1：已过期
    status = db.Column(db.SmallInteger, default=1)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    def __repr__(self):
        return '<SubscribeService %r>' % self.id
        

class SubscribeRecord(db.Model):
    """应用服务订购记录"""

    __tablename__ = 'service_transactions'

    id = db.Column(db.Integer, primary_key=True)

    master_uid = db.Column(db.Integer, default=0)
    service_id = db.Column(db.Integer, db.ForeignKey('app_services.id'))
    
    sale_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    pay_mode = db.Column(db.SmallInteger, default=1)
    # 根据订阅方式，折扣价格
    discount_money = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 订购时间
    ordered_at = db.Column(db.Integer, default=timestamp)
    # 订购天数, 15天试用期
    ordered_days = db.Column(db.Integer, default=15)
    
    