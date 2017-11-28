# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from app.models import User, Product

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/cart')
@auth.login_required
def get_cart():
    """获取当前购物车"""
    pass


@api.route('/cart', method=['POST'])
@auth.login_required
def addto_cart():
    """加入到购物车"""
    pass


@api.route('/cart', method=['PUT'])
@auth.login_required
def update_cart():
    """更新购物车信息"""
    pass


@api.route('/cart', methods=['DELETE'])
@auth.login_required
def clear_cart():
    """清空购物车"""
    pass

