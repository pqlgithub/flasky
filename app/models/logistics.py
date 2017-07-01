# -*- coding: utf-8 -*-

from app import db
from ..utils import timestamp

__all__ = [
    'Express',
    'Shipper'
]

class Express(db.Model):
    """物流公司信息"""

    __tablename__ = 'expresses'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    name = db.Column(db.String(32), index=True, nullable=False)
    # 联系人信息
    contact_name = db.Column(db.String(16), nullable=False)
    contact_mobile = db.Column(db.String(11))
    contact_phone = db.Column(db.String(20))
    description = db.Column(db.String(255))

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<Express %r>' % self.name


class Shipper(db.Model):
    """物流发货人"""

    __tablename__ = 'shippers'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)

    name = db.Column(db.String(32), nullable=False)
    phone = db.Column(db.String(32))
    mobile = db.Column(db.String(32))
    zipcode = db.Column(db.Integer)
    # 始发地
    from_city = db.Column(db.String(32), index=True, nullable=False)
    province = db.Column(db.String(32))
    city = db.Column(db.String(32))
    area = db.Column(db.String(32))
    address = db.Column(db.String(128), nullable=False)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<Shipper %r>' % self.name



