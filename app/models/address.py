# -*- coding: utf-8 -*-
from app import db
from ..models import Country
from ..utils import timestamp

__all__ = [
    'Address'
]

class Address(db.Model):
    """收货地址薄"""
    
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    
    master_uid = db.Column(db.Integer, index=True, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    country = db.Column(db.Integer, default=0)
    
    province = db.Column(db.String(100))
    city_id = db.Column(db.Integer, default=0)
    city = db.Column(db.String(50))
    area_id = db.Column(db.Integer, default=0)
    area = db.Column(db.String(50))
    street_address = db.Column(db.String(150))
    street_address_two = db.Column(db.String(150))
    zipcode = db.Column(db.String(10))
    
    # 是否默认
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    
    @property
    def ship_country(self):
        return Country.query.get(self.country)
    
    
    def __repr__(self):
        return '<Address {}>'.format(self.id)
    