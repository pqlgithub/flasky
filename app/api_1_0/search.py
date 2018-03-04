# -*- coding: utf-8 -*-
from flask import request, abort, url_for, g
from flask_sqlalchemy import Pagination

from .. import db
from . import api
from .utils import *
from app.models import SearchHistory, Product
from app.tasks import update_search_history


@api.route('/search/products', methods=['POST'])
def search_products():
    """搜索商品列表"""
    page = request.json.get('page', 1)
    per_page = request.json.get('per_page', 10)
    qk = request.json.get('qk')

    if not qk:
        abort(404)

    builder = Product.query.filter_by(master_uid=g.master_uid)

    qk = qk.strip()
    if qk:
        builder = builder.whoosh_search(qk, like=True)

    products = builder.order_by(Product.updated_at.desc()).all()

    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    paginated_products = products[start:end]

    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    # 任务：自动加入搜索历史
    update_search_history.apply_async(args=[qk, g.master_uid, total_count])

    return full_response(R200_OK, {
        'qk': qk,
        'total_count': total_count,
        'prev': pagination.has_prev,
        'next': pagination.has_next,
        'paginated_products': [product.to_json() for product in paginated_products]
    })


@api.route('/search/history')
def search_history():
    """搜索历史"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    prev_url = None
    next_url = None

    builder = SearchHistory.query.filter_by(master_uid=g.master_uid)

    pagination = builder.order_by(SearchHistory.search_at.desc()).paginate(page, per_page, error_out=False)

    search_items = pagination.items
    if pagination.has_prev:
        prev_url = url_for('api.search_history', page=page - 1, _external=True)

    if pagination.has_next:
        next_url = url_for('api.search_history', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'search_items': [sh.to_json() for sh in search_items],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })
