# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from . import main
from .. import db
from app.models import WxPreAuthCode, WxAuthCode
from app.forms import H5mallForm
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
    back_url = 'http://127.0.0.1:9000/open/wx/authorize_callback'
    auth_type = 3

    wx_code = WxPreAuthCode.query.first()

    authorize_url = ('https://mp.weixin.qq.com/cgi-bin/componentloginpage?component_appid={}&pre_auth_code={}&'
                     'redirect_uri={}&auth_type={}').format(app_id, wx_code.pre_auth_code, back_url, auth_type)

    return redirect(authorize_url)
