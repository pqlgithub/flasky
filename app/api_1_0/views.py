# -*- coding: utf-8 -*-
"""
    views.py
	~~~~~~~~~~~~~~
	公共服务接口

	:copyright: (c) 2017 by mic.
"""
from flask import request, abort, g, url_for
from app.models import User, Product, Country, Banner

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/countries')
def get_countries():
    """获取开放的国家"""
    countries = Country.query.filter_by(status=True).all()
    
    return full_response(R204_NOCONTENT, [country.to_json() for country in countries])


@api.route('/common/slides')
def get_slide():
    """大图轮换列表"""
    spot = request.values.get('spot')
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 3, type=int)
    
    if not spot:
        abort(404)
    
    banner_spot = Banner.query.filter_by(master_uid=g.master_uid, serial_no=spot, status=1).first()
    
    if banner_spot is None:
        abort(404)
        
    banners = banner_spot.images.order_by('updated_at desc').limit(per_page).all()
    
    return full_response(R200_OK, {
        'slides': [banner.to_json() for banner in banners],
    })


@api.route('/demo')
def demo():
    """测试示例"""
    resp = jsonify({'error': False})
    # 跨域设置
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
