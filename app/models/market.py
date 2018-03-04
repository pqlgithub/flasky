# -*- coding: utf-8 -*-
from sqlalchemy import event
from flask_babelex import lazy_gettext
from app import db
from .asset import Asset
from ..utils import timestamp
from ..constant import SERVICE_TYPES
from app.helpers import MixGenId

__all__ = [
    'AppService',
    'SubscribeService',
    'SubscribeRecord',
    'ApplicationStatus',
    'Invitation',
    'Bonus'
]

# 产品的状态
STORE_STATUS = [
    (1, lazy_gettext('Enabled'), 'success'),
    (-1, lazy_gettext('Disabled'), 'danger')
]


class ApplicationStatus:
    # 通过审核
    ENABLED = 2
    # 等待审核
    PENDING = 1
    # 禁用
    DISABLED = -1


# 应用的状态
APPLICATION_STATUS = [
    (ApplicationStatus.ENABLED, lazy_gettext('Published'), 'success'),
    (ApplicationStatus.PENDING, lazy_gettext('Pending'), 'success'),
    (ApplicationStatus.DISABLED, lazy_gettext('Disabled'), 'danger')
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
    status = db.Column(db.SmallInteger, default=ApplicationStatus.PENDING)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def status_label(self):
        for s in APPLICATION_STATUS:
            if s[0] == self.status:
                return s

    @property
    def type_label(self):
        for s in SERVICE_TYPES:
            if s[0] == self.type:
                return s

    @property
    def icon(self):
        """logo asset info"""
        return Asset.query.get(self.icon_id) if self.icon_id else Asset.default_logo()
    
    def mark_set_published(self):
        """发布上架状态"""
        self.status = ApplicationStatus.ENABLED
        
    def mark_set_disabled(self):
        """设置禁用状态"""
        self.status = ApplicationStatus.DISABLED
    
    @staticmethod
    def make_unique_sn():
        """生成品牌编号"""
        sn = MixGenId.gen_app_sn()
        if AppService.query.filter_by(serial_no=sn).first() is None:
            return sn
        
        while True:
            new_sn = MixGenId.gen_app_sn()
            if AppService.query.filter_by(serial_no=new_sn).first() is None:
                break
        return new_sn

    @staticmethod
    def on_before_insert(mapper, connection, target):
        # 自动生成用户编号
        target.serial_no = AppService.make_unique_sn()

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
    

class Invitation(db.Model):
    """邀请注册好礼"""

    __tablename__ = 'invitations'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    code = db.Column(db.String(16), nullable=False)
    user_id = db.Column(db.Integer, default=0)
    
    used_by = db.Column(db.Integer, default=0)
    # 是否使用
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    def __repr__(self):
        return '<Invitation {}>'.format(self.id)


class Bonus(db.Model):
    """促销红包"""

    __tablename__ = 'bonus'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    code = db.Column(db.String(16), nullable=False)
    amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 过期时间
    expired_at = db.Column(db.Integer, default=0)
    # 限制最近消费金额
    min_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 限制使用某个商品
    product_rid = db.Column(db.String(12), nullable=True)
    # 活动编号
    xname = db.Column(db.String(8), nullable=True)
    # 状态
    status = db.Column(db.SmallInteger, default=0)
    
    # 所属人
    user_id = db.Column(db.Integer, default=0)
    # 获得时间
    get_at = db.Column(db.Integer, default=0)
    
    # 使用者
    used_by = db.Column(db.Integer, default=0)
    used_at = db.Column(db.Integer, default=0)
    is_used = db.Column(db.Boolean, default=False)
    # 使用在某个订单上
    order_rid = db.Column(db.String(12), nullable=True)
    
    def __repr__(self):
        return '<Bonus {}>'.format(self.code)


# 监听Brand事件
event.listen(AppService, 'before_insert', AppService.on_before_insert)