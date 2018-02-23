# -*- coding: utf-8 -*-
from flask import redirect, url_for, current_app, render_template, flash
from . import adminlte
from .. import db, cache
from app.models import WxToken, WxAuthCode
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

    component_verify_ticket = cache.get('wx_component_verify_ticket')
    if component_verify_ticket is None:
        return custom_response(True, "Component verify ticket isn't exist!!!")

    try:
        # 发起请求
        wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                           component_app_secret=current_app.config['WX_APP_SECRET'])

        result = wx_app_api.get_component_token(component_verify_ticket)

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

