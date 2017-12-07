# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext
from jieba.analyse.analyzer import ChineseAnalyzer
import flask_whooshalchemyplus
from app import db
from ..utils import timestamp
from ..constant import CUSTOMER_STATUS, DISCOUNT_TEMPLET_TYPES

__all__ = [
    'Customer',
    'CustomerGrade',
    'ProductPacket',
    'DiscountTemplet',
    'DiscountTempletItem'
]

# customer and product => N to N
customer_packet_table = db.Table('customer_packets',
    db.Column('customer_id', db.Integer, db.ForeignKey('customers.id')),
    db.Column('product_packet_id', db.Integer, db.ForeignKey('product_packets.id'))
)

# product and product_packet => N to N
product_packet_table = db.Table('packet_products',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
    db.Column('product_packet_id', db.Integer, db.ForeignKey('product_packets.id'))
)


class Customer(db.Model):
    """分销客户"""
    
    __tablename__ = 'customers'

    __searchable__ = ['name', 'sn', 'mobile']
    __analyzer__ = ChineseAnalyzer()
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    name = db.Column(db.String(20), nullable=False)
    sn = db.Column(db.String(20), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('customer_grades.id'))
    
    province = db.Column(db.String(100))
    city = db.Column(db.String(50))
    area = db.Column(db.String(50))
    street_address = db.Column(db.String(150))
    zipcode = db.Column(db.String(10))
    mobile = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100), nullable=False)
    qq = db.Column(db.String(50))
    
    # 状态：禁用：-1；待审核：1；审核：2
    status = db.Column(db.SmallInteger, default=1)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def status_label(self):
        for s in CUSTOMER_STATUS:
            if s[0] == self.status:
                return s
    
    def __repr__(self):
        return '<Customer {}>'.format(self.name)
    
    
    
class CustomerGrade(db.Model):
    """分销商等级"""
    
    __tablename__ = 'customer_grades'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    name = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    # grade => customer 1 => N
    customers = db.relationship(
        'Customer', backref='customer_grade', lazy='dynamic'
    )
    
    
    def __repr__(self):
        return '<CustomerGrade {}>'.format(self.name)
    

class ProductPacket(db.Model):
    """商品包"""

    __tablename__ = 'product_packets'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)

    name = db.Column(db.String(20), nullable=False)
    
    discount_templet_id = db.Column(db.Integer, db.ForeignKey('discount_templets.id'))
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    
    def __repr__(self):
        return '<ProductPacket {}>'.format(self.name)
    

class DiscountTemplet(db.Model):
    """折扣模板"""
    
    __tablename__ = 'discount_templets'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    name = db.Column(db.String(20), nullable=False)
    default_discount = db.Column(db.Numeric(precision=10, scale=2), default=100.00)
    # 计算方式
    type = db.Column(db.SmallInteger, default=1)
    description = db.Column(db.String(200))

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    
    @property
    def type_label(self):
        for t in DISCOUNT_TEMPLET_TYPES:
            if self.type == t[0]:
                return t
    
    # discount_templet => product_packets 1 to N
    product_packets = db.relationship(
        'ProductPacket', backref='discount_templet', lazy='dynamic', cascade='delete'
    )

    # discount_templet and items => 1 to N
    items = db.relationship(
        'DiscountTempletItem', backref='discount_templet', lazy='dynamic', cascade='delete'
    )
    
    def __repr__(self):
        return '<DiscountTemplet {}>'.format(self.name)
    
    
class DiscountTempletItem(db.Model):
    """折扣模板明细"""

    __tablename__ = 'discount_templet_items'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    discount_templet_id = db.Column(db.Integer, db.ForeignKey('discount_templets.id'))
    
    category_id = db.Column(db.Integer, default=0)
    brand_id = db.Column(db.Integer, default=0)
    discount = db.Column(db.Numeric(precision=10, scale=2), default=100.00)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    
    def __repr__(self):
        return '<DiscountTempletItem {}>'.format(self.id)