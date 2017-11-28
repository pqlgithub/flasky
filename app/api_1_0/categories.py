# -*- coding: utf-8 -*-
from flask import g, current_app, request, url_for, abort
from app.models import Category
from app import db
from . import api
from .utils import *

@api.route('/categories')
def get_categories():
    """
    全部分类列表
    
    :return: json
    """
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Category.query.filter_by(master_uid=g.master_uid).paginate(page, per_page=per_page, error_out=False)
    categories = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_categories', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_categories', page=page + 1, _external=True)
        
    return full_response(R200_OK, {
        'categories': [category.to_json() for category in categories],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/categories/<int:id>')
def get_category(id):
    """
    分类详情信息
    
    :param id: 分类Id
    :return: json
    """
    category = Category.query.get_or_404(id)
    return full_response(R200_OK, category.to_json())

@api.route('/categories', methods=['POST'])
def create_category():
    """
    新增分类
    当请求以 JSON 格式形式，request.json 才会有请求的数据
    
    :return: json
    """
    current_app.logger.debug(request.json)
    if not request.json or not 'name' in request.json:
        abort(400)
    
    # 添加master_uid
    request.json['master_uid'] = g.master_uid
    
    category = Category.from_json(request.json)
    
    db.session.add(category)
    db.session.commit()
    
    return full_response(R201_CREATED, category.to_json())


@api.route('/categories/<int:id>', methods=['PUT'])
def edit_category(id):
    """
    更新分类信息
    
    :param id: 分类Id
    :return: json
    """
    category = Category.query.get_or_404(id)
    
    category.name = request.json.get('name', category.name)
    
    db.session.add(category)
    
    return full_response(R200_OK, category.to_json())