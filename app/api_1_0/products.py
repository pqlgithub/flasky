# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Brand, Product, Category, Customer, ProductPacket, ProductSku


@api.route('/products')
def get_products():
    """获取全部或某分类下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    category_id = request.values.get('cid', type=int)
    prev_url = None
    next_url = None
    
    if category_id:
        category = Category.query.get(category_id)
        if category is None or category.master_uid != g.master_uid:
            abort(404)
        builder = category.products.filter_by(master_uid=g.master_uid)
    else:
        builder = Product.query.filter_by(master_uid=g.master_uid)
    
    pagination = builder.order_by(Product.updated_at.desc()).paginate(page, per_page, error_out=False)
    
    products = pagination.items
    if pagination.has_prev:
        prev_url = url_for('api.get_products', cid=category_id, page=page-1, _external=True)
        
    if pagination.has_next:
        next_url = url_for('api.get_products', cid=category_id, page=page+1, _external=True)
    
    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/products/latest')
def get_latest_products():
    """获取最新商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)

    builder = Product.query.filter_by(master_uid=g.master_uid)
    pagination = builder.order_by(Product.created_at.desc()).paginate(page, per_page, error_out=False)
    products = pagination.items

    return full_response(R200_OK, {
        'products': [product.to_json() for product in products]
    })


@api.route('/products/sticked')
def get_sticked_products():
    """获取推荐商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    prev_url = None
    next_url = None

    builder = Product.query.filter_by(master_uid=g.master_uid, sticked=True)
    pagination = builder.order_by(Product.created_at.desc()).paginate(page, per_page, error_out=False)
    products = pagination.items
    if pagination.has_prev:
        prev_url = url_for('api.get_sticked_products', page=page - 1, _external=True)

    if pagination.has_next:
        next_url = url_for('api.get_sticked_products', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/products/by_brand/<string:rid>')
def get_products_by_brand(rid):
    """获取某品牌下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    prev_url = None
    next_url = None

    # 品牌是否存在
    brand = Brand.query.filter_by(sn=rid).first()
    if brand is None:
        return custom_response('品牌不存在', 401, False)
    
    builder = Product.query.filter_by(master_uid=g.master_uid, brand_id=brand.id)
    pagination = builder.order_by(Product.updated_at.desc()).paginate(page, per_page, error_out=False)
    products = pagination.items
    
    if pagination.has_prev:
        prev_url = url_for('api.get_products_by_brand', rid=rid, page=page - 1, _external=True)

    if pagination.has_next:
        next_url = url_for('api.get_products_by_brand', rid=rid, page=page + 1, _external=True)
        
    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/products/by_customer/<string:rid>')
def get_products_by_customer(rid):
    """获取某分销商下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    prev_url = None
    next_url = None
    
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
        .filter(Product.master_uid == g.master_uid).filter(ProductPacket.id.in_(distribute_packet_ids))

    pagination = builder.order_by(Product.updated_at.desc()).paginate(page, per_page, error_out=False)
    products = pagination.items
    
    if pagination.has_prev:
        prev_url = url_for('api.get_products_by_customer', rid=rid, page=page - 1, _external=True)

    if pagination.has_next:
        next_url = url_for('api.get_products_by_customer', rid=rid, page=page + 1, _external=True)

    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })
    

@api.route('/products/<string:rid>')
def get_product(rid):
    """获取单个商品信息"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if product is None:
        abort(404)
    
    # 添加品牌信息
    brand = product.brand
    
    # 商品详情
    content = product.details.content if product.details else ''
    
    result = product.to_json()
    result['content'] = content
    result['brand'] = brand.to_json()
    
    return full_response(R200_OK, result)


@api.route('/products/by_sku')
def get_product_by_sku():
    """通过Sku获取商品信息"""
    sku_rid = request.values.get('rid')
    if not sku_rid:
        abort(404)
    
    sku_rids = sku_rid.split(',')
    builder = ProductSku.query.filter_by(master_uid=g.master_uid)
    product_skus = builder.filter(ProductSku.serial_no.in_(sku_rids)).all()
    if product_skus is None:
        abort(404)
    
    return full_response(R200_OK, [sku.to_json() for sku in product_skus])


@api.route('/products/<string:rid>/detail')
def get_product_detail(rid):
    """获取商品的内容详情"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if product is None:
        abort(404)

    product_details = product.details.to_json() if product.details else {}

    return full_response(R200_OK, product_details)


@api.route('/products/skus')
def get_product_skus():
    """获取商品的Skus"""
    rid = request.values.get('rid')
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if product is None:
        abort(404)
        
    modes = []
    colors = []
    items = []
    for sku in product.skus:
        if sku.s_model:
            modes.append(sku.s_model)
            
        if sku.s_color:
            colors.append(sku.s_color)
        
        items.append({
            'rid': sku.serial_no,
            'mode': sku.mode,
            'product_name': product.name,
            's_model': sku.s_model,
            's_color': sku.s_color,
            'cover': sku.cover.view_url,
            'price': str(sku.price),
            'cost_price': str(sku.cost_price),
            'sale_price': str(sku.sale_price),
            's_weight': str(sku.s_weight),
            'stock_count': sku.stock_count
        })
        
    # 去除重复元素
    modes = [{'name': m, 'valid': True} for m in list(set(modes))]
    colors = [{'name': c, 'valid': True} for c in list(set(colors))]
    product_skus = {
        'modes': modes,
        'colors': colors,
        'items': items
    }
    
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

