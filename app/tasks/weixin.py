# -*- coding: utf-8 -*-
"""
    weixin.py
    微信第三方平台相关任务
"""
import json
from flask import current_app
from app.extensions import fsk_celery

from app import db, cache
from app.models import WxToken, WxAuthorizer, WxAuthCode
from app.helpers import WxApp, WxAppError
from app.utils import timestamp

FAIL = 'FAIL'
SKIP = 'SKIP'
SUCCESS = 'SUCCESS'


@fsk_celery.task(name='wx.refresh_component_token')
def refresh_component_token():
    """定时刷新component access token, 在令牌快过期时（比如1小时50分）再进行刷新"""
    current_app.logger.warn('start check refresh wx token...')
    component_app_id = current_app.config['WX_APP_ID']
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
    if wx_token is None:
        current_app.logger.warn("Component access token isn't exist!!!")
        return FAIL

    # 检测是否过期
    now_time = int(timestamp())
    if wx_token.created_at + wx_token.expires_in - 600 > now_time:
        current_app.logger.debug("Component access token not expired!")
        return SKIP

    # 发起请求
    component_verify_ticket = cache.get('wx_component_verify_ticket')
    if component_verify_ticket is None:
        current_app.logger.warn("Component verify ticket isn't exist!!!")
        return FAIL

    wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                       component_app_secret=current_app.config['WX_APP_SECRET'])
    result = wx_app_api.get_component_token(component_verify_ticket)

    # 更新数据
    wx_token.access_token = result.component_access_token
    wx_token.expires_in = result.expires_in
    wx_token.created_at = int(timestamp())

    db.session.commit()

    return SUCCESS


@fsk_celery.task(name='wx.refresh_authorizer_token')
def refresh_authorizer_token():
    """2小时刷新一次授权小程序的接口调用凭据（令牌）"""
    current_app.logger.warn('start refresh authorizer token...')

    expired_time = int(timestamp()) - 6600  # 1小时50分时刷新
    authorizer_list = WxAuthorizer.query.filter(WxAuthorizer.created_at < expired_time).all()
    if authorizer_list is None:
        current_app.logger.warn("Authorizer list hasn't expired!")
        return SKIP

    try:
        # 发起请求
        component_app_id = current_app.config['WX_APP_ID']
        wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
        if wx_token is None:
            current_app.logger.warn("Refresh: authorizer access_token isn't exist!!!")
            return FAIL

        wx_app_api = WxApp(component_app_id, current_app.config['WX_APP_SECRET'], wx_token.access_token)

        for authorizer in authorizer_list:
            result = wx_app_api.get_authorizer_token(authorizer.auth_app_id, authorizer.refresh_token)

            # 更新access token
            authorizer.access_token = result.authorizer_access_token
            authorizer.created_at = int(timestamp())

        db.session.commit()

    except WxAppError as err:
        current_app.logger.warn('Refresh authorizer token error: %s' % err)
        return FAIL

    return SUCCESS
