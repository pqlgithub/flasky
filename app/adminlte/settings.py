# -*- coding: utf-8 -*-
from flask import redirect, url_for, current_app, render_template
from . import adminlte
from .. import db
from app.models import WxTicket, WxToken
from app.helpers import WxApp


@adminlte.route('/settings')
def setting_index():
    return render_template('adminlte/settings/index.html')


@adminlte.route('/wx/init_token')
def get_weixin_token():
    """初始化微信第三方平台component_access_token"""
    wx_ticket = WxTicket.query.order_by(WxTicket.created_at.desc()).first()
    if wx_ticket is None:
        current_app.logger.warn("Component verify ticket isn't exist!!!")
        return False

    current_app.logger.warn('app_id: %s , app_secret: %s' % (current_app.config['WX_APP_ID'],
                                                             current_app.config['WX_APP_SECRET']))
    # 发起请求
    wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                       component_app_secret=current_app.config['WX_APP_SECRET'])

    result = wx_app_api.get_component_token(wx_ticket.ticket)

    current_app.logger.debug('Response: %s' % result)

    # 更新数据
    wx_token = WxToken(
        app_id=current_app.config['WX_APP_ID'],
        access_token=result.get('component_access_token'),
        expires_in=result.get('expires_in')
    )
    db.session.add(wx_token)

    db.session.commit()

    return render_template('adminlte/weixin/get_token.html',
                           access_token=result.get('component_access_token'))