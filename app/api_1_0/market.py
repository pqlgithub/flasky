# -*- coding: utf-8 -*-
from flask import request, abort, url_for, g, current_app
from sqlalchemy.exc import IntegrityError

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Bonus
from app.utils import datestr_to_timestamp, timestamp


@api.route('/market/bonus')
def get_bonus_list():
    """获取红包列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    used = request.values.get('used', 'N01')
    status = request.values.get('status', 1)
    
    builder = Bonus.query.filter_by(master_uid=g.master_uid, status=status)
    if used == 'N01':  # 未使用
        builder = builder.filter_by(is_used=False)
    elif used == 'N03':  # 已过期
        builder = builder.filter(Bonus.expired_at < int(timestamp()))
    else:  # 已使用
        builder = builder.filter_by(is_used=True)

    pagination = builder.paginate(page, per_page=per_page, error_out=False)
    bonus_list = pagination.items
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_bonus_list', page=page - 1, _external=True)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_bonus_list', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'bonus_list': [bonus.to_json() for bonus in bonus_list],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/market/user_bonus')
@auth.login_required
def get_user_bonus():
    """获取用户红包列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    status = request.values.get('status', 'N01')

    builder = Bonus.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id)
    if status == 'N01':  # 未使用
        builder = builder.filter_by(is_used=False)
    elif status == 'N03':  # 已过期
        builder = builder.filter(Bonus.expired_at < int(timestamp()))
    else:  # 已使用
        builder = builder.filter_by(is_used=True)

    pagination = builder.paginate(page, per_page=per_page, error_out=False)
    bonus_list = pagination.items
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_user_bonus', page=page - 1, _external=True)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_user_bonus', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'bonus_list': [bonus.to_json() for bonus in bonus_list],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/market/bonus/<string:rid>')
@auth.login_required
def get_bonus(rid):
    """获取红包信息"""
    bonus = Bonus.query.filter_by(master_uid=g.master_uid, code=rid).first()
    if bonus is None:
        return status_response(R404_NOTFOUND, False)

    return full_response(R200_OK, bonus.to_json())


@api.route('/market/bonus/grant', methods=['POST'])
@auth.login_required
def grant_bonus():
    """授予红包信息"""
    if not request.json or 'rid' not in request.json:
        abort(400)
    rid = request.json.get('rid')
    bonus = Bonus.query.filter_by(master_uid=g.master_uid, code=rid).first()
    if bonus is None:
        return status_response(R404_NOTFOUND, False)
    if bonus.status != 1:
        return custom_response('该红包已被领取！', 401, False)
    bonus.grant_bonus(g.current_user.id)
    db.session.commit()

    return full_response(R200_OK, bonus.to_json())


@api.route('/market/bonus/create', methods=['POST'])
@auth.login_required
def create_bonus():
    """添加新红包"""
    if not request.json or 'amount' not in request.json:
        abort(400)

    # todo: 验证用户身份，必须主账号权限用户

    # todo: 数据验证
    quantity = request.json.get('quantity')
    expired_at = request.json.get('expired_at')
    if expired_at:
        expired_at = datestr_to_timestamp(expired_at)

    try:
        for idx in range(quantity):
            bonus = Bonus(
                master_uid=g.master_uid,
                amount=request.json.get('amount'),
                expired_at=expired_at,
                min_amount=request.json.get('min_amount'),
                xname=request.json.get('xname'),
                product_rid=request.json.get('product_rid'),
                status=request.json.get('status')
            )
            db.session.add(bonus)

        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Create bonus fail: {}'.format(str(err)))

        db.session.rollback()
        return status_response(custom_status('Create failed!', 400), False)

    return full_response(R201_CREATED, bonus.to_json())


@api.route('/market/bonus/<string:rid>/disabled', methods=['POST'])
@auth.login_required
def disabled_brand(rid):
    """禁用红包"""
    bonus = Bonus.query.filter_by(master_uid=g.master_uid, code=rid).first()
    if bonus is None:
        abort(404)

    bonus.mark_set_disabled()

    db.session.commit()

    return status_response(R200_OK)

