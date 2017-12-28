# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext
from app import db
from ..utils import timestamp

__all__ = [
    'Address',
    'Country',
    'Place'
]

# 地址的状态
PLACE_STATUS = [
    (True, lazy_gettext('Enabled'), 'success'),
    (False, lazy_gettext('Disabled'), 'danger')
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
    mobile = db.Column(db.String(20))
    
    # 所属国家
    country_id = db.Column(db.Integer, default=0)
    province_id = db.Column(db.Integer, default=0)
    province = db.Column(db.String(100))
    city_id = db.Column(db.Integer, default=0)
    city = db.Column(db.String(50))
    town_id = db.Column(db.Integer, default=0)
    town = db.Column(db.String(50))
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
        return Country.query.get(self.country_id)
    
    
    def __repr__(self):
        return '<Address {}>'.format(self.id)


class Country(db.Model):
    """开通的国家列表"""
    
    __tablename__ = 'countries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    en_name = db.Column(db.String(128), index=True, nullable=False)
    code = db.Column(db.String(16), index=True, nullable=False)
    code2 = db.Column(db.String(16), nullable=True)
    # 是否开通
    status = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    def __repr__(self):
        return '<Country %r>' % self.code


class Place(db.Model):
    """省市城市地域地址"""
    
    __tablename__ = 'places'
    
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'))
    
    name = db.Column(db.String(100), nullable=False)
    # 所属父级
    pid = db.Column(db.Integer, default=0)
    layer = db.Column(db.SmallInteger, default=1)
    sort_by = db.Column(db.Integer, default=1)
    
    # 状态：显示 True; 隐藏 False
    status = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    
    @property
    def status_label(self):
        for s in PLACE_STATUS:
            if s[0] == self.status:
                return s

    @staticmethod
    def find_parent(pid=0, tree=[]):
        """递归获取父级"""
        if not pid:
            return tree
        
        place = Place.query.get(pid)
        if place:
            tree.insert(0, place.name)
            if place.pid:
                return Place.find_parent(place.pid, tree)
        
        return tree
    
    @staticmethod
    def provinces(pid=0):
        """获取所有一级省市列表"""
        builder = Place.query.filter_by(layer=1)
        if pid:
            builder = builder.filter_by(pid=pid)
        
        return builder.order_by(Place.sort_by.asc()).all()
    
    @staticmethod
    def cities(pid=0):
        """获取所有二级市区列表"""
        builder = Place.query.filter_by(layer=2)
        if pid:
            builder = builder.filter_by(pid=pid)

        return builder.order_by(Place.sort_by.asc()).all()
    
    @staticmethod
    def towns(pid=0):
        """获取所有三级城镇列表"""
        builder = Place.query.filter_by(layer=3)
        if pid:
            builder = builder.filter_by(pid=pid)

        return builder.order_by(Place.sort_by.asc()).all()
    
    @staticmethod
    def areas(pid=0):
        """获取所有四级区域列表"""
        builder = Place.query.filter_by(layer=4)
        if pid:
            builder = builder.filter_by(pid=pid)
        
        return builder.order_by(Place.sort_by.asc()).all()
        
    
    def __repr__(self):
        return '<Area {}>'.format(self.name)
