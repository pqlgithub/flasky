# -*- coding: utf-8 -*-
from app import db


__all__ = [
    'MasterStatistics',
    'StoreStatistics'
]

class MasterStatistics(db.Model):
    """ 公司销售统计表 """
    __tablename__ = 'master_statistics'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, nullable=False)
    income = db.Column(db.Numeric(precision=10, scale=2),default=0.00)
    profit = db.Column(db.Numeric(precision=10, scale=2),default=0.00)
    type = db.Column(db.SmallInteger, nullable=False)
    time = db.Column(db.String(8),nullable=False)
    income_yoy = db.Column(db.Numeric(precision=10, scale=2),nullable=True)
    income_mom = db.Column(db.Numeric(precision=10, scale=2),nullable=True)
    profit_yoy = db.Column(db.Numeric(precision=10, scale=2),nullable=True)
    profit_mom = db.Column(db.Numeric(precision=10, scale=2),nullable=True)

    __table_args__ = (
        db.Index('master_uid','time'),
    )

    def __repr__(self):
        return '<MasterStatistics %r>' % self.id



class StoreStatistics(db.Model):
    """ 店铺销售统计表 """
    __tablename__ = 'store_statistics'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, nullable=False)
    store_id = db.Column(db.Integer, index=True, nullable=False)
    income = db.Column(db.Numeric(precision=10, scale=2),default=0.00)
    profit = db.Column(db.Numeric(precision=10, scale=2),default=0.00)
    type = db.Column(db.SmallInteger, nullable=False)
    time = db.Column(db.String(8),nullable=False)
    income_yoy = db.Column(db.Numeric(precision=10, scale=2),nullable=True)
    income_mom = db.Column(db.Numeric(precision=10, scale=2),nullable=True)
    profit_yoy = db.Column(db.Numeric(precision=10, scale=2),nullable=True)
    profit_mom = db.Column(db.Numeric(precision=10, scale=2),nullable=True)

    __table_args__ = (
        db.Index('master_uid','time','store_id'),
    )

    def __repr__(self):
        return '<StoreStatistics %r>' % self.id
