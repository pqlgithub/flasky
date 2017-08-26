# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp
from ..constant import SUPPORT_PLATFORM

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
