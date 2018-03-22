# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError
from app.models import Customer, CustomerGrade, User, UserIdType

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.helpers import MixGenId


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

    try:

        new_sn = MixGenId.gen_customer_sn()

        # 首先添加分销客户
        user = User()
        user.email = request.json.get('account')
        user.username = request.json.get('name')
        user.password = request.json.get('pwd')
        user.time_zone = 'zh'
        user.id_type = UserIdType.CUSTOMER

        db.session.add(user)

        # 同步保存客户基本信息
        customer_info = request.json
        # 添加 master_uid
        customer_info['master_uid'] = g.master_uid
        customer_info['user_id'] = g.current_user.id
        customer_info['sn'] = new_sn

        # 保存客户信息
        customer = Customer.create(customer_info, user)
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
    json_obj = request.json

    customer = Customer.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    if customer is None:
        abort(404)
    
    try:
        customer.name = json_obj.get('name', customer.name)
        customer.grade_id = json_obj.get('grade_id', customer.grade_id)
        customer.province = json_obj.get('province', customer.province)
        customer.city = json_obj.get('city', customer.city)
        customer.area = json_obj.get('area', customer.area)
        customer.street_address = json_obj.get('street_address', customer.street_address)
        customer.zipcode = json_obj.get('zipcode', customer.zipcode)
        customer.mobile = json_obj.get('mobile', customer.mobile)
        customer.phone = json_obj.get('phone', customer.phone)
        customer.email = json_obj.get('email', customer.email)
        customer.qq = json_obj.get('qq', customer.qq)

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


@api.route('/customer_grades')
def get_customer_grades():
    """获取客户等级列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = CustomerGrade.query.filter_by(master_uid=g.master_uid).paginate(page, per_page, error_out=False)
    customer_grades = pagination.items
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_customer_grades', page=page - 1, _external=True)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_customer_grades', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'grades': [grade.to_json() for grade in customer_grades],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/customer_grades', methods=['POST'])
@auth.login_required
def create_grade():
    """添加客户等级"""
    if not request.json or 'name' not in request.json:
        abort(400)

    # todo: 数据验证

    try:
        grade = CustomerGrade(
            master_uid=g.master_uid,
            name=request.json.get('name')
        )
        db.session.add(grade)
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Create customer grade fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Create grade failed!', 400), False)

    return full_response(R201_CREATED, grade.to_json())


@api.route('/customer_grades/<int:rid>', methods=['PUT'])
@auth.login_required
def update_grade(rid):
    """更新客户等级信息"""
    grade = CustomerGrade.query.filter_by(master_uid=g.master_uid, id=rid).first()
    if grade is None:
        abort(404)

    try:
        # 更新name
        grade.name = request.json.get('name')
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Update customer grade fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Update grade failed!', 400), False)

    return full_response(R200_OK, grade.to_json())


@api.route('/customer_grades/<int:rid>', methods=['DELETE'])
@auth.login_required
def delete_grade(rid):
    """删除分销客户"""
    grade = CustomerGrade.query.filter_by(master_uid=g.master_uid, id=rid).first()
    if grade is None:
        abort(404)

    # 检测是否已被使用
    if grade.customers.count():
        return status_response({
            'code': 403,
            'message': '此等级已被使用，不能删除！'
        }, False)

    db.session.delete(grade)
    db.session.commit()

    return status_response(R200_OK)
