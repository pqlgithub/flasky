# -*- coding: utf-8 -*-
"""
    views.py
	~~~~~~~~~~~~~~
	公共服务接口

	:copyright: (c) 2017 by mic.
"""
from flask import request, abort, g, url_for
from app.models import User, Product

from .. import db
from . import api
from .auth import auth
from .utils import *


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
