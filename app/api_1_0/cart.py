# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError
from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Cart


@api.route('/cart')
@auth.login_required
def get_cart():
    """获取当前购物车"""
    cart_items = Cart.query.filter_by(master_uid=g.master_uid).all()
    if cart_items is None:
        abort(404)
    
    total_quantity = 0
    items = []
    for item in cart_items:
        total_quantity += item.quantity
        items.append(item.to_json())
    
    return full_response(R200_OK, {
        'total_quantity': total_quantity,
        'items': items
    })


@api.route('/cart', methods=['POST'])
@auth.login_required
def addto_cart():
    """加入到购物车"""
    sku_rid = request.json.get('rid')
    quantity = request.json.get('quantity', 1)
    option = request.json.get('option')
    
    # 检测是否存在某商品
    cart = Cart.query.filter_by(master_uid=g.master_uid,user_id=g.current_user.id,sku_rid=sku_rid).first()
    if not cart:
        cart = Cart(
            master_uid=g.master_uid,
            user_id=g.current_user.id,
            sess_id=str(g.master_uid),  # 备用
            sku_rid=sku_rid,
            option=option,
            quantity=quantity
        )
        db.session.add(cart)
    else: # 已存在，则更新信息
        cart.quantity = quantity
        cart.option = option

    try:
        db.session.commit()
    except (IntegrityError) as err:
        current_app.logger.error('Addto cart fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Addto failed!', 400), False)

    return full_response(R201_CREATED, cart.to_json())


@api.route('/cart', methods=['PUT'])
@auth.login_required
def update_cart():
    """加入到购物车"""
    sku_rid = request.json.get('rid')
    quantity = request.json.get('quantity', 1)
    option = request.json.get('option')
    
    # 检测是否存在某商品
    cart = Cart.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id, sku_rid=sku_rid).first()
    if cart is None:
        abort(404)
    
    # 更新信息
    cart.quantity = quantity
    cart.option = option
    
    try:
        db.session.commit()
    except (IntegrityError) as err:
        current_app.logger.error('Update cart fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Update failed!', 400), False)
    
    return full_response(R200_OK, cart.to_json())


@api.route('/cart/<string:rid>/remove', methods=['POST'])
@auth.login_required
def remove_cart(rid):
    cart = Cart.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id, sku_rid=rid).first()
    if cart is None:
        abort(404)
    try:
        db.session.delete(cart)
        db.session.commit()
    except (IntegrityError) as err:
        current_app.logger.error('Remove cart fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Remove failed!', 400), False)
    
    return status_response(R204_NOCONTENT)
    

@api.route('/cart', methods=['DELETE'])
@auth.login_required
def clear_cart():
    """清空购物车"""
    cart_items = Cart.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id).all()
    if cart_items:
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()
    
    return status_response(R204_NOCONTENT)
    
