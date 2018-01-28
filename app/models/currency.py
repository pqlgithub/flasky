# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp
from ..textex import LOCAL_TEXTS

__all__ = [
    'Currency'
]


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

    @property
    def fx_title(self):
        """本地化转换"""
        if self.title.startswith('fx_'):
            return LOCAL_TEXTS.get(self.title) if self.title in LOCAL_TEXTS.keys() else self.title

        return self.title

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_currency = {
            'id': self.id,
            'title': self.fx_title,
            'code': self.code,
            'symbol_left': self.symbol_left,
            'value': self.value
        }
        return json_currency

    def __repr__(self):
        return '<Currency {}>'.format(self.id)
