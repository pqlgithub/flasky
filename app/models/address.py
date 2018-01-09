# -*- coding: utf-8 -*-
from sqlalchemy import text, event
from flask_babelex import lazy_gettext
from app import db
from app.helpers import MixGenId
from app.exceptions import ValidationError
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
    serial_no = db.Column(db.String(11), unique=True, index=True, nullable=True)
    
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
    def full_name(self):
        return ''.join([self.first_name, self.last_name])
    
    @property
    def country(self):
        return Country.query.get(self.country_id)

    @staticmethod
    def make_unique_serial_no():
        serial_no = MixGenId.gen_address_sn(9)
        if Address.query.filter_by(serial_no=serial_no).first() is None:
            return serial_no
        while True:
            new_serial_no = MixGenId.gen_address_sn(9)
            if Address.query.filter_by(serial_no=new_serial_no).first() is None:
                break
        return new_serial_no
    
    @staticmethod
    def on_sync_change(mapper, connection, target):
        """同步事件"""
        if target.province_id:
            province_row = Place.query.get(target.province_id)
            target.province = province_row.name if province_row else ''
            target.country_id = province_row.country_id
        if target.city_id:
            city_row = Place.query.get(target.city_id)
            target.city = city_row.name if city_row else ''
        if target.town_id:
            town_row = Place.query.get(target.town_id)
            target.town = town_row.name if town_row else ''
        if target.area_id:
            area_row = Place.query.get(target.area_id)
            target.area = area_row.name if area_row else ''
    
    
    @staticmethod
    def validate_required_fields(json_address):
        """验证必须数据格式"""
        # 数据验证
        first_name = json_address.get('first_name')
        last_name = json_address.get('last_name')
        if first_name is None and last_name is None:
            raise ValidationError("Name can't empty!")
        
        if json_address.get('province_id') is None:
            raise ValidationError("Province can't empty!")
        
        return True
    
    
    @staticmethod
    def from_json(json_address):
        """从json格式数据创建，对API支持"""
        
        if not Address.validate_required_fields(json_address):
            raise ValidationError("Fields validate error!")
        
        return Address(
            first_name=json_address.get('first_name'),
            last_name=json_address.get('last_name'),
            phone=json_address.get('phone'),
            mobile=json_address.get('mobile'),
            province_id=json_address.get('province_id'),
            city_id=json_address.get('city_id'),
            town_id=json_address.get('town_id'),
            area_id=json_address.get('area_id'),
            street_address=json_address.get('street_address'),
            street_address_two=json_address.get('street_address_two'),
            zipcode=json_address.get('zipcode'),
            is_default=bool(json_address.get('is_default'))
        )
    
    
    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'rid': self.serial_no,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'mobile': self.mobile,
            'province': self.province,
            'city': self.city,
            'town': self.town,
            'area': self.area,
            'street_address': self.street_address,
            'street_address_two': self.street_address_two,
            'zipcode': self.zipcode,
            'is_default': self.is_default
        }
        return json_obj
    
    
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
    
    
    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'rid': self.id,
            'name': self.name,
            'en_name': self.en_name,
            'code': self.code,
            'code2': self.code2
        }
        return json_obj
    
    
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
    
    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'rid': self.id,
            'name': self.name,
            'pid': self.pid,
            'sort_by': self.sort_by,
            'status': self.status
        }
        return json_obj
    
    def __repr__(self):
        return '<Area {}>'.format(self.name)


# 添加监听事件, 实现触发器
event.listen(Address, 'before_insert', Address.on_sync_change)
event.listen(Address, 'before_update', Address.on_sync_change)