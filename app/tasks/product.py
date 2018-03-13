# -*- coding: utf-8 -*-
from sqlalchemy import text, event
from sqlalchemy.sql import func
from flask import current_app
from app.extensions import fsk_celery

from app import db
from app.models import Product, SearchHistory, ProductSku, Purchase, SupplyStats, ProductStock
from .conn import session

FAIL = 'FAIL'
SKIP = 'SKIP'
SUCCESS = 'SUCCESS'


@fsk_celery.task(name='product.update_search_history')
def update_search_history(qk, uid, total_count=0, user_id=0):
    """新增或更新搜索历史记录"""

    current_app.logger.warn('Task: update search[%s] history' % qk)

    history = SearchHistory.query.filter_by(master_uid=uid, query_word=qk).first()
    if history is None:
        # 新增
        history = SearchHistory(
            master_uid=uid,
            user_id=user_id,
            query_word=qk,
            total_count=total_count
        )
        db.session.add(history)
    else:
        history.total_count = total_count
        history.search_times += 1

    db.session.commit()

    return SUCCESS


@fsk_celery.task(name='product.sync_product_stock')
def sync_product_stock(product_id):
    """同步商品库存数"""
    current_app.logger.warn('Task: sync product[%s] stock' % product_id)

    product = session.query(Product).get(int(product_id))
    if product is None:
        current_app.logger.warn('Task: sync product[%s] stock, not exist!' % product_id)
        return FAIL

    total_stock = 0
    for sku in product.skus:
        total_stock += sku.stock_quantity

    current_app.logger.warn('total stock: %d' % total_stock)

    # 更新库存
    if product.total_stock != total_stock:
        product.total_stock = total_stock

    session.commit()

    return SUCCESS


@fsk_celery.task(name='product.sync_sku_stock')
def sync_sku_stock(sku_id):
    """同步商品sku库存数"""
    current_app.logger.warn('Task: sync sku[%s] stock' % sku_id)
    # sku总库存数
    stock_quantity = ProductStock.stock_count_of_product(sku_id)

    # 1、更新数据
    sku = session.query(ProductSku).get(sku_id)
    sku.stock_quantity = stock_quantity

    # 2、同步更新产品库存数
    product_id = sku.product_id
    product = session.query(Product).get(int(product_id))
    if product is None:
        current_app.logger.warn('Task: sync sku-product[%s] stock, not exist!' % product_id)
        return FAIL

    total_stock = 0
    for sku in product.skus:
        total_stock += sku.stock_quantity

    current_app.logger.warn('total stock: %d' % total_stock)

    # 更新库存
    if product.total_stock != total_stock:
        product.total_stock = total_stock

    session.commit()

    return SUCCESS


@fsk_celery.task(name='product.sync_supply_stats')
def sync_supply_stats(master_uid, supplier_id):
    """同步供货关系"""
    # 无供应商信息则跳过，如免费版不强制设置供应商
    if not supplier_id:
        current_app.logger.warn('Task: sync supply[%d], not exist!' % supplier_id)
        return FAIL

    # 1、统计sku count
    sku_count = session.query(ProductSku).filter_by(master_uid=master_uid, supplier_id=supplier_id).count()

    # 2、统计purchase / 总收入
    purchase_result = session.query(Purchase).filter_by(master_uid=master_uid, supplier_id=supplier_id) \
        .with_entities(func.count(Purchase.id), func.sum(Purchase.total_amount), func.max(Purchase.created_at)) \
        .one()

    purchase_amount = purchase_result[1] if purchase_result[1] is not None else 0
    latest_trade_at = purchase_result[2] if purchase_result[2] is not None else 0

    # 3、同步数据
    supply_stats = session.query(SupplyStats).filter_by(master_uid=master_uid, supplier_id=supplier_id).first()
    if supply_stats:
        supply_stats.sku_count = sku_count
        supply_stats.purchase_times = purchase_result[0]
        supply_stats.purchase_amount = purchase_amount
        supply_stats.latest_trade_at = latest_trade_at
    else:
        supply_stats = SupplyStats(
            master_uid=master_uid,
            supplier_id=supplier_id,
            sku_count=sku_count,
            purchase_times=purchase_result[0],
            purchase_amount=purchase_amount,
            latest_trade_at=latest_trade_at
        )
        session.add(supply_stats)

    session.commit()

    return SUCCESS
