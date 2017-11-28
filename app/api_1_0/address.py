# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from app.models import User, Product

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/address')
@auth.login_required
def get_addresses():
    """获取用户收货地址"""
    pass


@api.route('/address/is_default')
@auth.login_required
def get_default_address():
    """获取用户默认收货地址"""
    pass


@api.route('/address', methods=['POST'])
@auth.login_required
def create_address():
    """新增用户收货地址"""
    pass


@api.route('/address/<string:rid>', methods=['PUT'])
@auth.login_required
def update_address(rid):
    """更新用户收货地址"""
    pass


@api.route('/address/<string:rid>/set_default', methods=['PUT'])
@auth.login_required
def mark_default_address(rid):
    """设置为默认地址"""
    pass


@api.route('/address/<string:rid>', methods=['DELETE'])
@auth.login_required
def delete_address(rid):
    """删除用户收货地址"""
    pass