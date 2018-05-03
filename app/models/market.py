# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sqlalchemy import event
from flask_babelex import lazy_gettext

from app import db
from .asset import Asset
from ..utils import timestamp, datestr_to_timestamp
from ..constant import SERVICE_TYPES
from app.helpers import MixGenId

__all__ = [
    'AppService',
    'EditionService',
    'SubscribeService',
    'ApplicationStatus',
    'Invitation',
    'Coupon',
    'UserCoupon',
    'Bonus'
]

# 产品的状态
STORE_STATUS = [
    (1, lazy_gettext('Enabled'), 'success'),
    (-1, lazy_gettext('Disabled'), 'danger')
]

# 优惠券类型
COUPON_TYPES = [
    (1, lazy_gettext('Standard'), 'success'),
    (2, lazy_gettext('Minimum'), 'warning'),
    (3, lazy_gettext('Subtraction'), 'danger')
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
    (ApplicationStatus.DISABLED, lazy_gettext('Disable'), 'danger')
]


class AppService(db.Model):
    """应用市场"""
    
    __tablename__ = 'app_services'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.String(10), unique=True, index=True)

    # 应用标识
    name = db.Column(db.String(30), unique=True, index=True)
    # 应用标题
    title = db.Column(db.String(50), nullable=False)
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
    is_free = db.Column(db.Boolean, default=True)
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

    def mark_set_pending(self):
        """待审状态"""
        self.status = ApplicationStatus.PENDING
        
    def mark_set_disabled(self):
        """设置禁用状态"""
        self.status = ApplicationStatus.DISABLED
    
    @staticmethod
    def make_unique_sn():
        """生成编号"""
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

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'rid': self.serial_no,
            'name': self.name,
            'title': self.title,
            'icon': self.icon.view_url,
            'summary': self.summary,
            'type': self.type,
            'type_label': self.type_label[1],
            'is_free': self.is_free,
            'sale_price': str(self.sale_price),
            'sale_count': self.sale_count
        }

        return json_obj

    def __repr__(self):
        return '<AppService %r>' % self.name


class SubscribeService(db.Model):
    """已订购的服务记录"""

    __tablename__ = 'subscribe_services'

    id = db.Column(db.Integer, primary_key=True)

    master_uid = db.Column(db.Integer, default=0)
    service_id = db.Column(db.Integer, db.ForeignKey('app_services.id'))
    service_serial_no = db.Column(db.String(10), index=True)

    # 交易编号
    trade_no = db.Column(db.String(20), unique=True, index=True, nullable=False)
    # 订购内容
    trade_content = db.Column(db.String(100), nullable=False)
    # 支付金额
    pay_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 总金额
    total_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 支付方式：1、微信支付；2、支付宝
    pay_mode = db.Column(db.SmallInteger, default=1)
    # 支付状态
    is_paid = db.Column(db.Boolean, default=False)
    # 根据订阅方式，折扣金额
    discount_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 订购时间
    ordered_at = db.Column(db.Integer, default=timestamp)
    # 订购天数, 15天试用期
    ordered_days = db.Column(db.Integer, default=15)
    # 优惠券码
    coupon_code = db.Column(db.String(16), nullable=True)
    # 状态 -1：已过期；1：正常
    status = db.Column(db.SmallInteger, default=1)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def expired_at(self):
        """过期时间"""
        if self.ordered_days == 1:
            return '永久'

        # 下单时间
        ordered_at = datetime.fromtimestamp(self.ordered_at)
        # 过期天数
        expired_in = ordered_at + timedelta(days=self.ordered_days)

        return expired_in.strftime("%Y-%m-%d %H:%S")

    def __repr__(self):
        return '<SubscribeService %r>' % self.id


class EditionService(db.Model):
    """某版本下包含的服务列表"""

    __tablename__ = 'edition_services'

    id = db.Column(db.Integer, primary_key=True)
    # 默认: 免费版
    edition_id = db.Column(db.SmallInteger, default=1)
    service_id = db.Column(db.Integer, db.ForeignKey('app_services.id'))

    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @staticmethod
    def services(edition_id):
        edition_services = EditionService.query.filter_by(edition_id=edition_id).all()

        service_ids = [edition_service.service_id for edition_service in edition_services]
        if service_ids:
            return AppService.query.filter(AppService.id.in_(service_ids)).all()

    def __repr__(self):
        return '<EditionService %r>' % self.id


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


class Coupon(db.Model):
    """优惠券"""

    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    # 优惠券名称
    name = db.Column(db.String(50), nullable=True)
    code = db.Column(db.String(16), nullable=False)
    # 面值
    amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 类型： 1、通用型；2、最低消费；3、满减
    type = db.Column(db.SmallInteger, default=1)
    # 限制最近消费金额
    min_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 满足金额
    reach_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    #  有效期
    start_date = db.Column(db.Integer, default=0)
    end_date = db.Column(db.Integer, default=0)
    # 限制使用某个商品
    product_rid = db.Column(db.String(12), nullable=True)
    # 领取数量
    got_count = db.Column(db.Integer, default=0)
    # 状态, -1: 禁用；1：正常；2：已结束
    status = db.Column(db.SmallInteger, default=0)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # N => N 转化为 1 => N
    user_coupons = db.relationship(
        'UserCoupon', backref='coupon', lazy='dynamic'
    )

    @property
    def type_label(self):
        for s in COUPON_TYPES:
            if s[0] == self.type:
                return s

    @property
    def type_text(self):
        if self.type == 3:
            s_label = '消费满{}元可减'.format(self.reach_amount)
        elif self.type == 2:
            s_label = '最低消费{}元可用'.format(self.min_amount)
        else:
            s_label = '全店通用'

        return s_label

    @staticmethod
    def make_unique_code():
        """生成红包代码"""
        code = MixGenId.gen_coupon_code(10)
        if Coupon.query.filter_by(code=code).first() is None:
            return code

        while True:
            new_code = MixGenId.gen_coupon_code(10)
            if Coupon.query.filter_by(code=new_code).first() is None:
                break
        return new_code

    @staticmethod
    def on_before_insert(mapper, connection, target):
        # 自动生成红包代码
        target.code = Coupon.make_unique_code()
        # 为空时，默认为0
        if not target.min_amount:
            target.min_amount = 0
        if not target.reach_amount:
            target.reach_amount = 0

        # 过期日期
        if target.start_date:
            target.start_date = datestr_to_timestamp(target.start_date)
        if target.end_date:
            target.end_date = datestr_to_timestamp(target.end_date)

    def mark_set_disabled(self):
        """禁用优惠券"""
        self.status = -1

    def to_json(self):
        json_obj = {
            'code': self.code,
            'amount': self.amount,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type': self.type,
            'type_text': self.type_text,
            'min_amount': self.min_amount,
            'reach_amount': self.reach_amount,
            'limit_products': self.product_rid,
            'name': self.name,
            'status': self.status,
            'created_at': self.created_at
        }
        return json_obj

    def __repr__(self):
        return '<Coupon {}>'.format(self.code)


class UserCoupon(db.Model):
    """用户与优惠券关联表"""

    __tablename__ = 'users_coupons'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'))
    # 获得时间
    get_at = db.Column(db.Integer, default=0)
    used_at = db.Column(db.Integer, default=0)
    is_used = db.Column(db.Boolean, default=False)
    # 使用在某个订单上
    order_rid = db.Column(db.String(12))
    created_at = db.Column(db.Integer, default=timestamp)

    def to_json(self):
        """返回json格式数据"""
        json_obj = {
            'get_at': self.get_at,
            'used_at': self.used_at,
            'is_used': self.is_used,
            'order_rid': self.order_rid,
            'coupon': self.coupon.to_json()
        }

        return json_obj

    def __repr__(self):
        return '<UserCoupon {}{}>'.format(self.user_id, self.coupon_id)


class Bonus(db.Model):
    """促销红包"""

    __tablename__ = 'bonus'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    code = db.Column(db.String(16), nullable=False)
    amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 类型： 1、通用红包；2、最低消费；3、满减
    type = db.Column(db.SmallInteger, default=1)
    # 过期时间
    expired_at = db.Column(db.Integer, default=0)
    # 限制最近消费金额
    min_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 满足金额
    reach_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 限制使用某个商品
    product_rid = db.Column(db.String(12), nullable=True)
    # 活动编号
    xname = db.Column(db.String(8), nullable=True)
    # 状态, -1: 禁用；1：正常；2：已颁发
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
    order_rid = db.Column(db.String(12), nullable=True, default='')

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def to_json(self):
        json_obj = {
            'code': self.code,
            'amount': self.amount,
            'expired_at': self.expired_at,
            'type': self.type,
            'min_amount': self.min_amount,
            'reach_amount': self.reach_amount,
            'limit_products': self.product_rid,
            'xname': self.xname,
            'status': self.status,
            'status_label': self.status_label,
            'user_id': self.user_id,
            'is_used': self.is_used,
            'created_at': self.created_at
        }
        return json_obj

    def __repr__(self):
        return '<Bonus {}>'.format(self.code)


# 监听AppService事件
event.listen(AppService, 'before_insert', AppService.on_before_insert)
event.listen(Coupon, 'before_insert', Coupon.on_before_insert)
