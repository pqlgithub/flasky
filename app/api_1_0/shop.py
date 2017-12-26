# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from app.models import Shop

from .. import db
from . import api
from .auth import auth
from .utils import *

@api.route('/shop/setting')
def get_shop():
    """获取微商城基本配置"""
    h5mall = Shop.query.filter_by(master_uid=g.master_uid).first()
    if h5mall is None:
        abort(404)
    
    return full_response(R200_OK, h5mall.to_json())