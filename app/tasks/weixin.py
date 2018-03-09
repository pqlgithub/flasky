# -*- coding: utf-8 -*-
"""
    weixin.py
    微信第三方平台相关任务
"""
import json
from flask import current_app
from app.extensions import fsk_celery

from app import db, cache
from app.models import WxToken, WxAuthorizer, Client, ClientStatus, Banner
from app.helpers import WxApp, WxAppError, WxaOpen3rd
from app.utils import timestamp, make_unique_key, make_pw_hash

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


@fsk_celery.task(name='wx.bind_wxa_tester')
def bind_wxa_tester(uid, auth_app_id, wx_account):
    """绑定体验者"""
    authorizer = WxAuthorizer.query.filter_by(master_uid=uid, auth_app_id=auth_app_id).first()
    if authorizer is None:
        current_app.logger.warn("Authorizer is't exist!")
        return FAIL
    access_token = authorizer.access_token

    try:
        open3rd = WxaOpen3rd(access_token=access_token)
        result = open3rd.bind_tester(wx_account)
    except WxAppError as err:
        current_app.logger.warn('Bind tester error: %s' % err)
        return FAIL

    return SUCCESS


@fsk_celery.task(name='wx.unbind_wxa_tester')
def unbind_wxa_tester(uid, auth_app_id, wx_account):
    """解绑体验者"""
    authorizer = WxAuthorizer.query.filter_by(master_uid=uid, auth_app_id=auth_app_id).first()
    if authorizer is None:
        current_app.logger.warn("Authorizer is't exist!")
        return FAIL
    access_token = authorizer.access_token

    try:
        open3rd = WxaOpen3rd(access_token=access_token)
        result = open3rd.unbind_tester(wx_account)
    except WxAppError as err:
        current_app.logger.warn('Unbind tester error: %s' % err)
        return FAIL

    return SUCCESS


@fsk_celery.task(name='wx.create_wxapi_appkey')
def create_wxapi_appkey(uid, name, store_id):
    """同步为小程序生成Api所需的key/secret"""
    if not uid or not store_id:
        return FAIL

    app_key = make_unique_key(20)
    client = Client(
        master_uid=uid,
        store_id=store_id,
        name=name,
        app_key=app_key,
        app_secret=make_pw_hash(app_key),
        status=ClientStatus.ENABLED
    )
    db.session.add(client)

    db.session.commit()

    return SUCCESS


@fsk_celery.task(name='wx.create_banner_spot')
def create_banner_spot(uid, serial_no, name, w=0, h=0):
    """同步为小程序创建banner位置"""
    if not uid or not serial_no or not name:
        return FAIL

    spot = Banner(
        master_uid=uid,
        serial_no=serial_no,
        name=name,
        width=w,
        height=h,
        status=1
    )
    db.session.add(spot)

    db.session.commit()

    return SUCCESS
