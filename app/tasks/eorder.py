# -*- coding: utf-8 -*-
from flask import current_app
from app.extensions import fsk_celery

from app import db
from app.models import Order, Cart, Coupon, UserCoupon
from app.utils import timestamp

FAIL = 'FAIL'
SKIP = 'SKIP'
SUCCESS = 'SUCCESS'


@fsk_celery.task(name='eorder.remove_order_cart')
def remove_order_cart(uid, rid):
    """下单成功，清除购物车记录"""

    current_app.logger.warn('Task: remove order[%s] cart' % rid)

    eorder = Order.query.filter_by(master_uid=uid, serial_no=rid).first()
    if eorder is None:
        return FAIL

    for item in eorder.items:
        # 删除购物车记录
        cart = Cart.query.filter_by(master_uid=uid, user_id=eorder.user_id, sku_rid=item.sku_serial_no).first()
        if cart:
            db.session.delete(cart)

    db.session.commit()

    return SUCCESS


@fsk_celery.task(name='eorder.update_coupon_status')
def update_coupon_status(uid, rid):
    """下单成功，更新使用优惠券的状态"""

    current_app.logger.warn('Task: update order[%s] coupon status' % rid)

    eorder = Order.query.filter_by(master_uid=uid, serial_no=rid).first()
    if eorder is None or not eorder.affiliate_code:
        return FAIL

    coupon = Coupon.query.filter_by(master_uid=uid, code=eorder.affiliate_code).first()
    if not coupon:
        return FAIL

    user_coupon = UserCoupon.query.filter_by(master_uid=uid, user_id=eorder.user_id, coupon_id=coupon.id).first()
    if not user_coupon:
        return FAIL

    # 更新优惠券的使用状态
    user_coupon.is_used = True
    user_coupon.used_at = int(timestamp())

    db.session.commit()

    return SUCCESS
