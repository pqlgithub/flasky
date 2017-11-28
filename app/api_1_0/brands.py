# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from app.models import User, Product, Brand

from .. import db
from . import api
from .auth import auth
from .utils import *

@api.route('/brands')
def get_brands():
    """获取品牌列表"""
    return "This is brands list."


@api.route('/brands/<string:rid>')
def get_brand(rid):
    """获取品牌信息"""
    pass


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

