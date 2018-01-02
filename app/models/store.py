# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext
from app import db
from ..utils import timestamp
from ..constant import SUPPORT_PLATFORM
from app.models import User

__all__ = [
    'Store',
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
    (1, lazy_gettext('Authorized Store')),
    (2, lazy_gettext('B2C E-commerce')),
    # 社交电商，如：小程序
    (3, lazy_gettext('Social E-commerce')),
    (5, lazy_gettext('Offline Store')),
    (6, lazy_gettext('Distribution'))
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
    # 类型：1、第三方店铺；2、自营；3、社交电商 5、实体店铺 6、分销
    type = db.Column(db.SmallInteger, default=1)
    # 状态 -1：禁用；1：正常
    status = db.Column(db.SmallInteger, default=1)
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
    

    @staticmethod
    def validate_unique_name(name, master_uid, platform):
        """验证店铺名称是否唯一"""
        return Store.query.filter_by(master_uid=master_uid, platform=platform, name=name).first()


    def __repr__(self):
        return '<Store %r>' % self.name