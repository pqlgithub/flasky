# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError
from app.models import Customer

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/customers')
def get_customers():
    """获取分销客户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Customer.query.filter_by(master_uid=g.master_uid).paginate(page, per_page=per_page, error_out=False)
    customers = pagination.items
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_customers', page=page - 1, _external=True)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_customers', page=page + 1, _external=True)
    
    return full_response(R200_OK, {
        'customers': [customer.to_json() for customer in customers],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/customers/<string:rid>')
def get_customer(rid):
    """获取分销客户信息"""
    customer = Customer.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    if customer is None:
        return status_response(R404_NOTFOUND, False)
    
    return full_response(R200_OK, customer.to_json())


@api.route('/customers', methods=['POST'])
@auth.login_required
def create_customer():
    """添加新分销客户"""
    if not request.json or 'name' not in request.json:
        abort(400)
    
    # todo: 数据验证
    
    customer = Customer.from_json(request.json)
    # 添加 master_uid
    customer.master_uid = g.master_uid
    
    try:
        db.session.add(customer)
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Create customer fail: {}'.format(str(err)))
        
        db.session.rollback()
        return status_response(custom_status('Create failed!', 400), False)
    
    return full_response(R201_CREATED, customer.to_json())


@api.route('/customers/<string:rid>', methods=['PUT'])
@auth.login_required
def update_customer(rid):
    """更新分销客户信息"""
    json_brand = request.json

    customer = Customer.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    if customer is None:
        abort(404)

    customer.name = json_brand.get('name', customer.name)
    
    try:
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Update customer fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Update failed!', 400), False)
    
    return full_response(R200_OK, customer.to_json())


@api.route('/customers/<string:rid>', methods=['DELETE'])
@auth.login_required
def delete_customer(rid):
    """删除分销客户"""
    customer = Customer.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    
    if customer is None:
        abort(404)
    
    db.session.delete(customer)
    
    return status_response(R200_OK)
