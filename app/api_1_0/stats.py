# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app

from .. import db
from . import api
from app.models import Shop, WxMiniApp, Store
from .auth import auth
from .utils import *


@api.route('/stats/report_master')
def get_master_report():
    """获取某个账户下总销售统计"""
    pass


@api.route('/stats/report_store')
def get_store_report():
    """获取某个店铺销售统计（日、周、当月）"""
    h5mall = Shop.query.filter_by(master_uid=g.master_uid).first()
    if h5mall is None:
        abort(404)

    return full_response(R200_OK, h5mall.to_json())


@api.route('/stats/report_top')
def get_product_top():
    """获取商品销售排行"""
    store_rid = request.values.get('store_rid')
    start_date = request.values.get('start_date')
    end_date = request.values.get('end_date')


