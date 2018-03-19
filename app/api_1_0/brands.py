# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError
from app.models import Brand

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/brands')
def get_brands():
    """获取品牌列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = Brand.query.filter_by(master_uid=g.master_uid).paginate(page, per_page=per_page, error_out=False)
    brands = pagination.items
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_brands', page=page - 1, _external=True)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_brands', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'brands': [brand.to_json() for brand in brands],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/brands/<string:rid>')
def get_brand(rid):
    """获取品牌信息"""
    brand = Brand.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    if brand is None:
        return status_response(R404_NOTFOUND, False)
    
    return full_response(R200_OK, brand.to_json())


@api.route('/brands', methods=['POST'])
@auth.login_required
def create_brand():
    """添加新品牌"""
    if not request.json or 'name' not in request.json:
        abort(400)
    
    # todo: 数据验证
    
    brand = Brand.from_json(request.json)
    # 添加 master_uid
    brand.master_uid = g.master_uid
    
    try:
        db.session.add(brand)
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Create brand fail: {}'.format(str(err)))
        
        db.session.rollback()
        return status_response(custom_status('Create failed!', 400), False)
    
    return full_response(R201_CREATED, brand.to_json())
    

@api.route('/brands/<string:rid>', methods=['PUT'])
@auth.login_required
def update_brand(rid):
    """更新品牌信息"""
    json_brand = request.json
    
    brand = Brand.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    if brand is None:
        abort(404)
    
    brand.name = json_brand.get('name', brand.name)
    brand.supplier_id = json_brand.get('supplier_id', brand.supplier_id)
    brand.features = json_brand.get('features', brand.features)
    brand.is_recommended = json_brand.get('is_recommended', brand.is_recommended)
    brand.sort_order = json_brand.get('sort_order', brand.sort_order)
    brand.description = json_brand.get('description', brand.description)
    
    try:
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Update brand fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Update failed!', 400), False)
    
    return full_response(R200_OK, brand.to_json())


@api.route('/brands/<string:rid>', methods=['DELETE'])
@auth.login_required
def delete_brand(rid):
    """删除品牌"""
    brand = Brand.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    
    if brand is None:
        abort(404)
    
    db.session.delete(brand)
    
    return status_response(R200_OK)
