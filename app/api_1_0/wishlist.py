# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Wishlist, Product


@api.route('/wishlist')
@auth.login_required
def get_wishlist():
    """获取收藏列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    prev_url = None
    next_url = None

    pagination = Wishlist.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id)\
        .order_by(Wishlist.created_at.desc()).paginate(page, per_page, error_out=False)
    if pagination.has_prev:
        prev_url = url_for('api.get_wishlist', page=page - 1, _external=True)

    if pagination.has_next:
        next_url = url_for('api.get_wishlist', page=page + 1, _external=True)

    products = []
    for item in pagination.items:
        product = Product.query.filter_by(master_uid=g.master_uid, serial_no=item.product_rid).first()
        if product:
            products.append(product.to_json())

    return full_response(R200_OK, {
        'products': products,
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/wishlist/addto', methods=['POST'])
@auth.login_required
def addto_wishlist():
    """添加到收藏"""
    product_rid = request.json.get('rid')
    if not product_rid:
        abort(400)

    wishlist = Wishlist.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id,
                                        product_rid=product_rid).first()
    if wishlist is None:
        # 新增
        wishlist = Wishlist(
            master_uid=g.master_uid,
            user_id=g.current_user.id,
            product_rid=product_rid
        )
        db.session.add(wishlist)

        db.session.commit()

    return status_response(R201_CREATED)


@api.route('/wishlist/remove', methods=['POST'])
@auth.login_required
def remove_wishlist():
    """移除收藏"""
    product_rid = request.json.get('rid')
    if not product_rid:
        abort(400)

    wishlist = Wishlist.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id,
                                        product_rid=product_rid).first()
    if wishlist:
        db.session.delete(wishlist)
        db.session.commit()

    return status_response(R204_NOCONTENT)
