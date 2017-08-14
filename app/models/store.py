# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp
from ..constant import SUPPORT_PLATFORM

__all__ = [
    'Store',
    'Country',
    'Currency'
]

class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)

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


    def __repr__(self):
        return '<Store %r>' % self.name



class Country(db.Model):
    """开通的国家列表"""

    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    cn_name = db.Column(db.String(128), index=True, nullable=False)
    en_name = db.Column(db.String(128), index=True, nullable=False)
    code = db.Column(db.String(16), index=True, nullable=False)
    code2 = db.Column(db.String(16), nullable=True)
    # 是否开通
    status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<Country %r>' % self.code


class Currency(db.Model):
    """支持币种"""

    __tablename__ = 'currencies'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    title = db.Column(db.String(32), unique=True, nullable=False)
    code = db.Column(db.String(3), nullable=False)
    symbol_left = db.Column(db.String(12), nullable=True)
    symbol_right = db.Column(db.String(12), nullable=True)
    decimal_place = db.Column(db.String(1), nullable=False)
    value = db.Column(db.Float(15, 8), nullable=False)
    status = db.Column(db.SmallInteger, default=1)

    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    last_updated = db.Column(db.Integer, default=timestamp)

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_currency = {
            'id': self.id,
            'title': self.title,
            'code': self.code,
            'symbol_left': self.symbol_left,
            'value': self.value
        }
        return json_currency

    def __repr__(self):
        return '<Currency {}>'.format(self.id)
