# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from app.models import User, Product

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/products')
def get_products():
    """获取全部或某分类下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    category_id = request.values.get('cid')
    prev = None
    next = None
    
    builder = Product.query.filter_by(master_uid=g.master_uid)

    pagination = builder.order_by('updated_at desc').paginate(page, per_page, error_out=False)
    products = pagination.items
    
    if pagination.has_prev:
        prev = url_for('api.get_products', page=page-1, _external=True)
        
    if pagination.has_next:
        next = url_for('api.get_products', page=page+1, _external=True)
    
    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/products/by_brand/<string:rid>')
def get_products_by_brand(rid):
    """获取某品牌下商品列表"""
    pass


@api.route('/products/<string:rid>')
def get_product(rid):
    """获取单个商品信息"""
    pass


@api.route('/products', methods=['POST'])
def create_product():
    """添加新的商品信息"""
    pass

@api.route('/products/<string:rid>', methods=['PUT'])
def update_product(rid):
    """更新商品信息"""
    pass


@api.route('/products/<string:rid>', methods=['DELETE'])
def delete_product(rid):
    """删除商品"""
    pass


