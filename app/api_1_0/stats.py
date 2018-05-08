# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app

from .. import db
from . import api
from app.models import Shop, WxMiniApp, Store
from .auth import auth
from .utils import *


@api.route('/stats/store_report')
def get_store_report():
    """获取某个店铺统计报表"""
    h5mall = Shop.query.filter_by(master_uid=g.master_uid).first()
    if h5mall is None:
        abort(404)

    return full_response(R200_OK, h5mall.to_json())
