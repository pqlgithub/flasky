# -*- coding: utf-8 -*-
from flask import redirect, url_for, current_app, render_template, flash
from . import adminlte
from .. import db
from app.models import WxTicket, WxToken, WxPreAuthCode, WxAuthCode
from app.helpers import WxApp, WxAppError
from app.utils import custom_response, timestamp


@adminlte.route('/settings')
def setting_index():
    return render_template('adminlte/settings/index.html')


@adminlte.route('/settings/weixin')
def setting_weixin():
    """配置微信第三方平台相关参数"""
    return render_template('adminlte/weixin/get_token.html')


@adminlte.route('/weixin/init_token')
def get_weixin_token():
    """初始化微信第三方平台component_access_token"""
    component_app_id = current_app.config['WX_APP_ID']
    is_exist = False
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
    if wx_token:
        # 检测是否过期
        now_time = int(timestamp())
        if wx_token.created_at + wx_token.expires_in - 600 > now_time:
            return custom_response(True, 'Component access token not expired!')
        is_exist = True

    wx_ticket = WxTicket.query.order_by(WxTicket.created_at.desc()).first()
    if wx_ticket is None:
        current_app.logger.warn("Component verify ticket isn't exist!!!")
        return custom_response(True, "Component verify ticket isn't exist!!!")

    try:
        # 发起请求
        wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                           component_app_secret=current_app.config['WX_APP_SECRET'])

        result = wx_app_api.get_component_token(wx_ticket.ticket)

        if is_exist:
            wx_token.access_token = result.component_access_token
            wx_token.expires_in = result.expires_in
            wx_token.created_at = int(timestamp())
        else:
            # 更新数据
            wx_token = WxToken(
                app_id=current_app.config['WX_APP_ID'],
                access_token=result.component_access_token,
                expires_in=result.expires_in
            )
            db.session.add(wx_token)

        db.session.commit()
    except WxAppError as err:
        current_app.logger.warn('Request weixin access token error: %s' % err)
        return custom_response(False, 'Request access token error: {}'.format(err))

    flash('刷新微信Access Token成功！', 'success')

    return redirect(url_for('.setting_weixin'))


@adminlte.route('/weixin/pre_auth_code')
def get_weixin_pre_code():
    """初始化微信第三方平台预授权码"""
    component_app_id = current_app.config['WX_APP_ID']
    pre_auth_code = WxPreAuthCode.query.first()
    is_exist = False
    if pre_auth_code:
        # 检测是否过期
        now_time = int(timestamp())
        if pre_auth_code.created_at + pre_auth_code.expires_in > now_time:
            return custom_response(True, 'Component pre_auth_code not expired!')
        is_exist = True

    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()

    try:
        # 发起请求
        wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                           component_app_secret=current_app.config['WX_APP_SECRET'],
                           component_access_token=wx_token.access_token)

        result = wx_app_api.get_pre_auth_code()

        if is_exist:
            pre_auth_code.access_token = result.pre_auth_code
            pre_auth_code.expires_in = result.expires_in
            pre_auth_code.created_at = int(timestamp())
        else:
            # 更新数据
            wx_pre_code = WxPreAuthCode(
                pre_auth_code=result.pre_auth_code,
                expires_in=result.expires_in
            )
            db.session.add(wx_pre_code)

        db.session.commit()
    except WxAppError as err:
        return custom_response(False, 'Request pre_auth_code error: {}'.format(err))

    flash('刷新预授权码成功！', 'success')

    return redirect(url_for('.setting_weixin'))
