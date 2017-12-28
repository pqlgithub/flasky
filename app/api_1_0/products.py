# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import User, Product, Category, Customer, ProductPacket, ProductSku


@api.route('/products')
def get_products():
    """获取全部或某分类下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    category_id = request.values.get('cid', type=int)
    prev = None
    next = None
    
    if category_id:
        category = Category.query.get(category_id)
        if category is None or category.master_uid != g.master_uid:
            abort(404)
        builder = category.products.filter_by(master_uid=g.master_uid)
    else:
        builder = Product.query.filter_by(master_uid=g.master_uid)
    
    pagination = builder.order_by('updated_at desc').paginate(page, per_page, error_out=False)
    
    products = pagination.items
    if pagination.has_prev:
        prev = url_for('api.get_products', cid=category_id, page=page-1, _external=True)
        
    if pagination.has_next:
        next = url_for('api.get_products', cid=category_id, page=page+1, _external=True)
    
    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/products/by_brand/<string:rid>')
def get_products_by_brand(rid):
    """获取某品牌下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    prev = None
    next = None
    
    builder = Product.query.filter_by(master_uid=g.master_uid, brand_rid=rid)
    pagination = builder.order_by('updated_at desc').paginate(page, per_page, error_out=False)
    products = pagination.items
    
    if pagination.has_prev:
        prev = url_for('api.get_products_by_brand', rid=rid, page=page - 1, _external=True)

    if pagination.has_next:
        next = url_for('api.get_products_by_brand', rid=rid, page=page + 1, _external=True)
        
    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/products/by_customer/<string:rid>')
def get_products_by_customer(rid):
    """获取某分销商下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    prev = None
    next = None
    
    current_customer = Customer.query.filter_by(master_uid=g.master_uid, sn=rid).first()
    if current_customer is None:
        abort(404)
    
    distribute_packet_ids = []
    for dp in current_customer.distribute_packets:
        distribute_packet_ids.append(dp.product_packet_id)
    
    if not distribute_packet_ids:
        abort(404)
    
    # 多对多关联查询
    builder = db.session.query(Product).join(ProductPacket, Product.product_packets)\
        .filter(Product.master_uid==g.master_uid).filter(ProductPacket.id.in_(distribute_packet_ids))

    pagination = builder.order_by(Product.updated_at.desc()).paginate(page, per_page, error_out=False)
    products = pagination.items
    
    if pagination.has_prev:
        prev = url_for('api.get_products_by_customer', rid=rid, page=page - 1, _external=True)

    if pagination.has_next:
        next = url_for('api.get_products_by_customer', rid=rid, page=page + 1, _external=True)

    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
    

@api.route('/products/<string:rid>')
def get_product(rid):
    """获取单个商品信息"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if product is None:
        abort(404)
    
    return full_response(R200_OK, product.to_json())


@api.route('/products/<string:rid>/detail')
def get_product_detail(rid):
    """获取商品的内容详情"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if product is None:
        abort(404)
    
    return full_response(R200_OK, product.details.to_json())

@api.route('/products/<string:rid>/skus')
def get_product_skus(rid):
    """获取商品的Skus"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if product is None:
        abort(404)
    
    product_skus = [sku.to_json() for sku in product.skus]
    
    return full_response(R200_OK, product_skus)
    

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


