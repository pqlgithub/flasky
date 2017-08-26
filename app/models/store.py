# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext
from app import db
from ..utils import timestamp
from ..constant import SUPPORT_PLATFORM
from app.models import User

__all__ = [
    'Store',
    'Country',
    'Currency'
]

# 产品的状态
STORE_STATUS = [
    (1, lazy_gettext('Enabled'), 'success'),
    (-1, lazy_gettext('Disabled'), 'danger')
]

class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    # 运营者
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
    def operator(self):
        """获取运营者信息"""
        return User.query.get(self.operator_id) if self.operator_id else None


    @staticmethod
    def validate_unique_name(name, master_uid, platform):
        """验证店铺名称是否唯一"""
        return Store.query.filter_by(master_uid=master_uid, platform=platform, name=name).first()


    def __repr__(self):
        return '<Store %r>' % self.name