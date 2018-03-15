# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app

from .. import db
from . import api
from app.models import Shop, WxMiniApp, Store
from .auth import auth
from .utils import *


@api.route('/store/h5mall')
def get_h5mall():
    """获取微商城基本配置"""
    h5mall = Shop.query.filter_by(master_uid=g.master_uid).first()
    if h5mall is None:
        abort(404)
    
    return full_response(R200_OK, h5mall.to_json())


@api.route('/store/wxapp')
def get_wxapp():
    """获取小程序基本信息"""
    store = Store.query.get_or_404(g.store_id)
    current_app.logger.debug('Wxapp {}'.format(store))

    if store.type != 3:  # 小程序
        abort(404)

    wxapp = WxMiniApp.query.filter_by(master_uid=g.master_uid, serial_no=store.serial_no).first()
    if wxapp is None:
        abort(404)

    return full_response(R200_OK, wxapp.to_json())

