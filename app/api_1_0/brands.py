# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
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
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_brands', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_brands', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'brands': [brand.to_json() for brand in brands],
        'prev': prev,
        'next': next,
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
    return 'new brand'


@api.route('/brands/<string:rid>', methods=['PUT'])
@auth.login_required
def update_brand(rid):
    """更新品牌信息"""
    pass


@api.route('/brands/<string:rid>', methods=['DELETE'])
@auth.login_required
def delete_brand(rid):
    """删除品牌"""
    pass

