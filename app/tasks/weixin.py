# -*- coding: utf-8 -*-
"""
    weixin.py
    微信第三方平台相关任务
"""
from flask import current_app
from app.extensions import fsk_celery

from app import db
from app.models import WxToken, WxTicket
from app.helpers import WxApp
from app.utils import timestamp


@fsk_celery.task(name='wx.refresh_component_token')
def refresh_component_token():
    """定时刷新component access token, 在令牌快过期时（比如1小时50分）再进行刷新"""
    current_app.logger.warn('start check refresh wx token...')
    component_app_id = current_app.config['WX_APP_ID']
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
    if wx_token is None:
        current_app.logger.warn("Component access token isn't exist!!!")
        return False

    # 检测是否过期
    now_time = int(timestamp())
    if wx_token.created_at + wx_token.expires_in - 600 > now_time:
        current_app.logger.debug("Component access token not expired!")
        return False

    # 发起请求
    wx_ticket = WxTicket.query.order_by(WxTicket.created_at.desc()).first()
    if wx_ticket is None:
        current_app.logger.warn("Component verify ticket isn't exist!!!")
        return False
    wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                       component_app_secret=current_app.config['WX_APP_SECRET'])

    result = wx_app_api.get_component_token(wx_ticket.ticket)

    # 更新数据
    wx_token.access_token = result.component_access_token
    wx_token.expires_in = result.expires_in
    wx_token.created_at = int(timestamp())

    db.session.commit()

    return True
