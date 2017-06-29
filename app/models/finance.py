# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp
from ..constant import TRANSACT_TYPE, TRANSACT_TARGET_TYPE
from app.models import Purchase

__all__ = [
    'PayAccount',
    'TransactDetail',
    'Invoice'
]

class PayAccount(db.Model):
    """支付账户"""

    __tablename__ = 'pay_accounts'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    bank = db.Column(db.String(50), nullable=False)
    account = db.Column(db.String(30), unique=True, nullable=False)
    remark = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return '<PayAccount %r>' % self.account


class TransactDetail(db.Model):
    """交易明细"""

    __tablename__ = 'transact_details'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    serial_no = db.Column(db.String(20), unique=True, index=True, nullable=False)
    # 付款人
    pay_account_id = db.Column(db.Integer, db.ForeignKey('pay_accounts.id'))
    # 收款人
    transact_user = db.Column(db.String(30), index=True, nullable=True)
    # 收支类型：1、收款 2、支付
    type = db.Column(db.SmallInteger, default=1)
    amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 关联ID: 采购单、退货单、订单
    target_id = db.Column(db.Integer, default=0)
    target_type = db.Column(db.SmallInteger, default=1)
    # 交易时间
    payed_at = db.Column(db.Integer, default=0)
    status = db.Column(db.SmallInteger, default=1)
    # 备注
    remark = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp)

    __table_args__ = (
        db.UniqueConstraint('target_id', 'target_type', name='uix_target_id_type'),
    )

    @property
    def status_label(self):
        if self.type == 2:
            return '已付款' if self.status == 2 else '待付款'
        if self.type == 1:
            return '已收款' if self.status == 2 else '待收款'


    @property
    def target(self):
        if self.target_type == 1:
            return Purchase.query.get(self.target_id)
        return None

    @property
    def target_type_label(self):
        for type in TRANSACT_TARGET_TYPE:
            if type[0] == self.target_type:
                return type


    def __repr__(self):
        return '<TransactDetail %r>' % self.id



class Invoice(db.Model):
    """发票信息"""

    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    # 用户ID
    master_uid = db.Column(db.Integer, index=True, default=0)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    title = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<Invoice %r>' % self.title