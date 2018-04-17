# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Brand, Product, Category, Customer, ProductPacket, ProductSku, Asset, Store, StoreProduct, \
    StoreDistributeProduct
from app.helpers import MixGenId


@api.route('/products')
def get_products():
    """获取全部或某分类下商品列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    category_id = request.values.get('cid', type=int)
    status = request.values.get('status', True, type=bool)
    
    if category_id:
        category = Category.query.get(category_id)
        if category is None or category.master_uid != g.master_uid:
            abort(404)
        builder = category.products.filter_by(master_uid=g.master_uid, status=status)
    else:
        builder = Product.query.filter_by(master_uid=g.master_uid, status=status)
    
    pagination = builder.order_by(Product.updated_at.desc()).paginate(page, per_page, error_out=False)
    products = pagination.items
    
    return full_response(R200_OK, {
        'products': [product.to_json() for product in products],
        'prev': pagination.has_prev,
        'next': pagination.has_next,
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


@api.route('/products/by_store')
def get_products_by_store():
    """获取某个店铺下商品列表"""
    rid = request.values.get('rid')
    cid = correct_int(request.values.get('cid'))
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 20, type=int)
    # 默认上架状态
    status = request.values.get('status', type=bool)

    current_store = Store.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if current_store is None:
        abort(404)

    products = []

    # 全品模式
    if current_store.distribute_mode == 1:
        if cid:
            category = Category.query.get(cid)
            if category is None or category.master_uid != g.master_uid:
                abort(404)
            builder = category.products.filter_by(master_uid=g.master_uid)
        else:
            builder = Product.query.filter_by(master_uid=g.master_uid)

        # 上架 或 下架 状态
        if status:
            builder = builder.filter_by(status=status)

        pagination = builder.order_by(Product.updated_at.desc()).paginate(page, per_page, error_out=False)

        products = [product.to_json() for product in pagination.items]

    # 部分授权
    if current_store.distribute_mode == 2:
        # 多对多关联查询
        if cid:
            builder = db.session.query(Product).filter(Product.master_uid == g.master_uid)
            # 店铺
            builder = builder.join(StoreProduct, StoreProduct.store_id == current_store.id)
            # 分类
            builder = builder.join(Category, Product.categories).filter(Category.id == cid)

            pagination = builder.order_by(StoreProduct.id.desc()).paginate(page, per_page, error_out=False)
            products = [product.to_json() for product in pagination.items]
        else:
            builder = StoreProduct.query.filter_by(master_uid=g.master_uid, store_id=current_store.id)

            pagination = builder.order_by(StoreProduct.id.desc()).paginate(page, per_page, error_out=False)
            for item in pagination.items:
                product = Product.query.get(item.product_id)
                if product:
                    products.append(product.to_json())

    return full_response(R200_OK, {
        'products': products,
        'prev': pagination.has_prev,
        'next': pagination.has_next,
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
    
    result = product.to_json()
    result['brand'] = brand.to_json() if brand else None
    
    return full_response(R200_OK, result)


@api.route('/products/by_sku')
def get_product_by_sku():
    """通过Sku获取商品信息"""
    sku_rid = request.values.get('rid')
    store_rid = request.values.get('store_rid')
    if not sku_rid:
        abort(404)
    
    sku_rids = sku_rid.split(',')
    builder = ProductSku.query.filter_by(master_uid=g.master_uid)
    product_skus = builder.filter(ProductSku.serial_no.in_(sku_rids)).all()
    if product_skus is None:
        abort(404)

    # 检测店铺是否有私有设置
    distribute_mode = 1
    if store_rid:
        current_store = Store.query.filter_by(master_uid=g.master_uid, serial_no=store_rid).first()
        if current_store and current_store.distribute_mode == 2:
            distribute_mode = current_store.distribute_mode

    skus = []
    for sku in product_skus:
        price = sku.price
        sale_price = sku.sale_price
        stock_count = sku.stock_count

        # 店铺为授权模式时，则获取私有设置
        if distribute_mode == 2:
            private_sku = StoreDistributeProduct.query.filter_by(master_uid=g.master_uid, store_id=current_store.id,
                                                                 sku_serial_no=sku.serial_no).first()
            if private_sku:
                price = private_sku.price if private_sku.price > 0 else price
                sale_price = private_sku.sale_price if private_sku.sale_price > 0 else sale_price
                # 店铺授权必须为私有库存
                stock_count = private_sku.private_stock

        sku = sku.to_json()

        # 覆盖数据
        sku['price'] = str(price)
        sku['sale_price'] = str(sale_price)
        sku['stock_count'] = stock_count

        skus.append(sku)

    return full_response(R200_OK, skus)


@api.route('/products/<string:rid>/detail')
def get_product_detail(rid):
    """获取商品的内容详情"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first()
    if product is None:
        abort(404)

    product_details = product.details.to_json() if product.details else {}

    # 检测展示图是否为空
    if not product_details.get('images') and product.cover_id:
        product_details['images'] = [product.cover.to_json()]

    return full_response(R200_OK, product_details)


@api.route('/products/skus')
def get_product_skus():
    """获取商品的Skus"""
    rid = request.values.get('rid')
    store_rid = request.values.get('store_rid')
    if not rid:
        abort(404)

    rids = rid.split(',')
    is_one = True if len(rids) == 1 else False

    builder = Product.query.filter_by(master_uid=g.master_uid)
    if is_one:
        products = builder.filter_by(serial_no=rids[0]).all()
    else:
        products = builder.filter(Product.serial_no.in_(rids)).all()

    if products is None:
        abort(404)

    # 检测店铺是否有私有设置
    distribute_mode = 1
    if store_rid:
        current_store = Store.query.filter_by(master_uid=g.master_uid, serial_no=store_rid).first()
        if current_store and current_store.distribute_mode == 2:
            distribute_mode = current_store.distribute_mode

    # 重组商品sku
    more_skus = {}
    for product in products:
        modes = []
        colors = []
        items = []
        for sku in product.skus:
            if sku.s_model and sku.s_model not in modes:
                modes.append(sku.s_model)

            if sku.s_color and sku.s_color not in colors:
                colors.append(sku.s_color)

            price = sku.price
            sale_price = sku.sale_price
            stock_count = sku.stock_count

            # 店铺为授权模式时，则获取私有设置
            if distribute_mode == 2:
                private_sku = StoreDistributeProduct.query.filter_by(master_uid=g.master_uid, store_id=current_store.id,
                                                                     sku_serial_no=sku.serial_no).first()
                if private_sku:
                    price = private_sku.price if private_sku.price > 0 else price
                    sale_price = private_sku.sale_price if private_sku.sale_price > 0 else sale_price
                    # 店铺授权必须为私有库存
                    stock_count = private_sku.private_stock

            items.append({
                'rid': sku.serial_no,
                'mode': sku.mode,
                'product_name': product.name,
                's_model': sku.s_model,
                's_color': sku.s_color,
                'cover': sku.cover.view_url,
                'price': str(price),
                'sale_price': str(sale_price),
                's_weight': str(sku.s_weight),
                'stock_count': stock_count
            })

        # 去除重复元素
        modes = [{'name': m, 'valid': True} for m in modes]
        colors = [{'name': c, 'valid': True} for c in colors]
        product_skus = {
            'modes': modes,
            'colors': colors,
            'items': items
        }

        more_skus[product.serial_no] = product_skus

    # 如果单一则直接返回单个
    if is_one:
        return full_response(R200_OK, more_skus[rid])
    
    return full_response(R200_OK, more_skus)


@api.route('/products', methods=['POST'])
@auth.login_required
def create_product():
    """添加新的商品信息"""
    if not request.json or 'name' not in request.json:
        abort(400)

    # todo: 数据验证
    # 同步保存商品基本信息
    data = request.json
    # 添加 master_uid
    data['master_uid'] = g.master_uid
    # 设置默认值
    if not request.json.get('cover_id'):
        default_cover = Asset.query.filter_by(is_default=True).first()
        data['cover_id'] = default_cover.id

    # 根据品牌获取供应商
    brand_id = request.json.get('brand_id')
    if brand_id:
        brand = Brand.query.filter_by(master_uid=g.master_uid, id=int(brand_id)).first()
        data['supplier_id'] = brand.supplier_id if brand else 0

    try:
        # 生成新sku
        new_sn = Product.make_unique_serial_no(MixGenId.gen_product_sku())
        data['serial_no'] = new_sn

        product = Product.create(data)
        db.session.add(product)

        # 更新所属分类
        category_id = request.json.get('category_id')
        if category_id:
            _categories = [Category.query.get(int(category_id))]
            product.update_categories(*_categories)

        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Create product fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Create failed!', 400), False)

    return full_response(R201_CREATED, product.to_json())


@api.route('/products/<string:rid>', methods=['PUT'])
@auth.login_required
def update_product(rid):
    """更新商品信息"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()

    # 同步保存商品基本信息
    data = request.json

    # 设置默认值
    if not request.json.get('cover_id'):
        default_cover = Asset.query.filter_by(is_default=True).first()
        data['cover_id'] = default_cover.id

    # 根据品牌获取供应商
    brand_id = request.json.get('brand_id')
    if brand_id:
        brand = Brand.query.filter_by(master_uid=g.master_uid, id=int(brand_id)).first()
        data['supplier_id'] = brand.supplier_id if brand else 0

    try:
        # 更新所属分类
        category_id = request.json.get('category_id')
        if category_id:
            _categories = [Category.query.get(int(category_id))]
            product.update_categories(*_categories)

        # 更新基本信息
        product.name = data.get('name', product.name)
        product.brand_id = data.get('brand_id', product.brand_id)
        product.supplier_id = data.get('supplier_id', product.supplier_id)
        product.cover_id = data.get('cover_id', product.cover_id)
        product.id_code = data.get('id_code', product.id_code)
        product.cost_price = data.get('cost_price', product.cost_price)
        product.price = data.get('price', product.price)
        product.sale_price = data.get('sale_price', product.sale_price)
        product.status = data.get('status', product.status)
        product.description = data.get('description', product.description)
        product.features = data.get('features', product.features)
        product.sticked = data.get('sticked', product.sticked)

        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Update product fail: {}'.format(str(err)))
        db.session.rollback()
        return status_response(custom_status('Update failed!', 400), False)

    return full_response(R201_CREATED, product.to_json())


@api.route('/products/<string:rid>', methods=['DELETE'])
@auth.login_required
def delete_product(rid):
    """删除商品"""
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()

    db.session.delete(product)

    return status_response(R200_OK)

