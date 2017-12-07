# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext
from jieba.analyse.analyzer import ChineseAnalyzer
import flask_whooshalchemyplus
from app import db
from ..utils import timestamp
from ..constant import CUSTOMER_STATUS

__all__ = [
    'Customer',
    'CustomerGrade'
]

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
    
    