# -*- coding: utf-8 -*-
"""
    views.py
	~~~~~~~~~~~~~~
	公共服务接口

	:copyright: (c) 2017 by mic.
"""
from flask import request, abort, g, url_for
from app.models import User, Product, Country

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/countries')
def get_countries():
    """获取开放的国家"""
    countries = Country.query.filter_by(status=True).all()
    
    return full_response(R204_NOCONTENT, [country.to_json() for country in countries])


@api.route('/common/slide')
def get_slide():
    """大图轮换列表"""
    pass


@api.route('/demo')
def demo():
    """测试示例"""
    resp = jsonify({'error': False})
    # 跨域设置
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
