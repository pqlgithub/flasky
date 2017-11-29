# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp

__all__ = [
    'Distributor',
    'DistributorGrade'
]

class Distributor(db.Model):
    """分销客户"""
    
    __tablename__ = 'distributors'
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)

    name = db.Column(db.String(20), nullable=False)
    sn = db.Column(db.String(20), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('distributor_grades.id'))
    
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
    
    
    def __repr__(self):
        return '<Distributor {}>'.format(self.name)
    
    
    
class DistributorGrade(db.Model):
    """分销商等级"""
    
    __tablename__ = 'distributor_grades'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    name = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    
    def __repr__(self):
        return '<DistributorGrade {}>'.format(self.name)
    
    