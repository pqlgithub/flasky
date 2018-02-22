# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from . import main
from .. import db, cache
from app.models import WxToken, WxPreAuthCode, WxAuthCode
from app.forms import H5mallForm
from app.helpers import WxApp, WxAppError
from ..utils import Master
from ..decorators import user_has, user_is


@main.route('/wxapp/setting', methods=['GET', 'POST'])
def wxapp_setting():
    """配置小程序参数"""
    pass


@main.route('/wxapp/authorize')
def wxapp_authorize():
    """跳转授权页"""
    app_id = current_app.config['WX_APP_ID']
    back_url = '{}/open/wx/authorize_callback'.format(current_app.config['DOMAIN_URL'])
    auth_type = 2

    # 1、获取预授权码
    pre_auth_code = _get_pre_auth_code()

    authorize_url = ('https://mp.weixin.qq.com/cgi-bin/componentloginpage?component_appid={}&pre_auth_code={}&'
                     'redirect_uri={}&auth_type={}').format(app_id, pre_auth_code, back_url, auth_type)

    return redirect(authorize_url)


@cache.cached(timeout=600, key_prefix='wx_pre_auth_code')
def _get_pre_auth_code():
    """获取预授权码"""
    current_app.logger.warn('get by caching...')
    component_app_id = current_app.config['WX_APP_ID']

    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()

    try:
        # 发起请求
        wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                           component_app_secret=current_app.config['WX_APP_SECRET'],
                           component_access_token=wx_token.access_token)

        result = wx_app_api.get_pre_auth_code()
    except WxAppError as err:
        current_app.logger.warn('Request pre_auth_code error: {}'.format(err))
        return None

    return result.pre_auth_code
