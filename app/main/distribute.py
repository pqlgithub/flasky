# -*- coding: utf-8 -*-
from flask import g, render_template, redirect, url_for, abort, flash, request
from . import main
from .. import db
from app.models import Product, Store, ProductDistribution, Category, StoreProduct, StoreDistributeProduct
from ..utils import Master, custom_response, correct_decimal, status_response
from ..decorators import user_has


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'market'
    }


@main.route('/fx_distribute/index')
def fx_distribute_index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 0, type=int)

    builder = Product.query.filter_by(is_distributed=True, status=True)
    paginated_products = builder.order_by(Product.updated_at.desc()).paginate(page, per_page)

    distribute_products = []
    for product in paginated_products.items:
        distribution_skus = ProductDistribution.query.filter_by(product_id=product.id).all()
        distribute_price = []
        suggested_min_price = []
        suggested_max_price = []
        for sku in distribution_skus:
            distribute_price.append(sku.distribute_price)
            suggested_min_price.append(sku.suggested_min_price)
            suggested_max_price.append(sku.suggested_max_price)

        extra_data = {
            'distribute_price': min(distribute_price),
            'profit': '%s ~ %s' % (max(suggested_min_price) - min(distribute_price),
                                   max(suggested_max_price) - min(distribute_price))
        }

        distribute_products.append(dict(product.to_json(), **extra_data))

    return render_template('fx_distribute/index.html',
                           status=status,
                           pagination=paginated_products,
                           paginated_products=paginated_products,
                           distribute_products=distribute_products,
                           **load_common_data())


@main.route('/fx_distribute/ajax_add', methods=['GET', 'POST'])
def fx_distribute_ajax_add():
    """添加分销"""
    rid = request.values.get('rid')
    if not rid:
        abort(404)

    product = Product.query.filter_by(serial_no=rid).first_or_404()
    # 验证是否开放分销
    if not product.is_distributed:
        abort(403)

    # 获取sku分销数据
    distribution_skus = ProductDistribution.query.filter_by(product_id=product.id).all()
    extra_data = {}
    for extra_sku in distribution_skus:
        extra_data[extra_sku.sku_serial_no] = {
            'distribute_price': extra_sku.distribute_price,
            'suggested_min_price': extra_sku.suggested_min_price,
            'suggested_max_price': extra_sku.suggested_max_price,
            'profit': str(extra_sku.suggested_min_price - extra_sku.distribute_price)
        }

    if request.method == 'POST':
        if product.master_uid == Master.master_uid():
            return custom_response(False, '自营产品不能自我分销！')

        # 验证是否开通小程序
        wxapp = Store.query.filter_by(master_uid=Master.master_uid(), platform=1).first()
        if wxapp is None:
            return custom_response(False, '小程序还没开通')

        # 商品与店铺的关系
        store_product = StoreProduct.query.filter_by(master_uid=Master.master_uid(), store_id=wxapp.id,
                                                     product_id=product.id).first()
        # 添加分销产品到店铺
        if store_product is None:
            store_product = StoreProduct(
                master_uid=Master.master_uid(),
                store_id=wxapp.id,
                product_id=product.id,
                is_distributed=True
            )
            db.session.add(store_product)

        # 添加分销产品售价
        for extra_sku in distribution_skus:
            price = correct_decimal(request.form.get('price_%s' % extra_sku.sku_serial_no))
            if not price or price < 0:
                return custom_response(False, '售价未设置或设置有误！')

            if price > extra_data[extra_sku.sku_serial_no]['suggested_max_price'] or \
                    price < extra_data[extra_sku.sku_serial_no]['suggested_min_price']:
                return custom_response(False, '售价设置与分销价格要求不符!')

            store_distribution = StoreDistributeProduct.query.filter_by(master_uid=Master.master_uid(),
                                                                        product_id=product.id,
                                                                        sku_id=extra_sku.product_sku_id).first()
            if store_distribution is None:
                store_distribution = StoreDistributeProduct(
                    master_uid=Master.master_uid(),
                    store_id=wxapp.id,
                    product_id=product.id,
                    product_serial_no=product.serial_no,
                    sku_id=extra_sku.product_sku_id,
                    sku_serial_no=extra_sku.sku_serial_no,
                    price=price
                )
                db.session.add(store_distribution)
            else:
                store_distribution.price = price

        db.session.commit()

        return status_response()

    # 获取店铺分类
    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())

    return render_template('fx_distribute/_modal_distribute_add.html',
                           paginated_categories=paginated_categories,
                           product=product,
                           extra_data=extra_data)


@main.route('/fx_distribute/product')
def fx_distribute_product():
    """分销商品详情"""
    rid = request.args.get('rid')
    product = Product.query.filter_by(serial_no=rid).first_or_404()

    # 获取sku分销数据
    distribution_skus = ProductDistribution.query.filter_by(product_id=product.id).all()
    extra_data = {}
    for extra_sku in distribution_skus:
        profit = []
        if extra_sku.suggested_min_price:
            profit.append(str(extra_sku.suggested_min_price - extra_sku.distribute_price))

        if extra_sku.suggested_max_price:
            profit.append(str(extra_sku.suggested_max_price - extra_sku.distribute_price))

        extra_data[extra_sku.sku_serial_no] = {
            'distribute_price': extra_sku.distribute_price,
            'suggested_min_price': extra_sku.suggested_min_price,
            'suggested_max_price': extra_sku.suggested_max_price,
            'profit': ' -- '.join(profit)
        }
