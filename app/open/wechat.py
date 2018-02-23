# -*- coding: utf-8 -*-
from flask import current_app, request, redirect, url_for
import xml.etree.cElementTree as ET

from . import open
from .. import db, cache
from app.models import WxAuthCode
from app.helpers import WXBizMsgCrypt, WxAppError, WxApp
from app.utils import Master, custom_response, timestamp
from app.tasks import exchange_authorizer_token


@open.route('/wx/authorize_notify', methods=['GET', 'POST'])
def authorize_notify():
    """接收取消授权通知、授权成功通知、授权更新通知"""
    signature = request.values.get('signature')
    encrypt_type = request.values.get('encrypt_type')
    timestamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')
    msg_signature = request.values.get('msg_signature')
    post_data = request.get_data()

    # 解密接口
    des_key = current_app.config['WX_APP_DES_KEY']
    token = current_app.config['WX_APP_TOKEN']
    app_id = current_app.config['WX_APP_ID']

    decrypt = WXBizMsgCrypt(token, des_key, app_id)
    ret, decrypt_content = decrypt.DecryptMsg(post_data, msg_signature, timestamp, nonce)
    # 解密成功
    if ret == 0:
        # 更新ticket
        current_app.logger.warn("decrypt content: %s" % decrypt_content)

        xml_tree = ET.fromstring(decrypt_content)
        info_type = xml_tree.find('InfoType').text
        app_id = xml_tree.find('AppId').text
        create_time = xml_tree.find('CreateTime').text

        current_app.logger.debug('Parse app_id:[%s], create_time[%s]' % (app_id, create_time))

        # 推送component_verify_ticket
        if info_type == 'component_verify_ticket':
            verify_ticket = xml_tree.find('ComponentVerifyTicket').text

            current_app.logger.debug('Component verify ticket: %s' % verify_ticket)

            # 设置缓存DB,每隔10分钟定时推送component_verify_ticket,
            # timeout是缓存过期时间，默认为0，永不过期
            cache.set('wx_component_verify_ticket', verify_ticket, timeout=0)

        # 推送授权成功消息
        elif info_type == 'authorized':
            authorizer_app_id = xml_tree.find('AuthorizerAppid').text
            authorizer_code = xml_tree.find('AuthorizationCode').text
            authorizer_expired_time = xml_tree.find('AuthorizationCodeExpiredTime').text

            current_app.logger.warn('Authorizer [%s][%s][%s]' % (authorizer_app_id, authorizer_code,
                                                                 authorizer_expired_time))
        else:
            pass

    else:
        current_app.logger.warn('error code: %d' % ret)

    return 'success'


@open.route('/wx/authorize_callback', methods=['GET'])
def authorize_callback():
    """授权成功后回调url"""
    current_app.logger.warn('request content {}'.format(request.values))

    auth_code = request.values.get('auth_code')
    expires_in = request.values.get('expires_in')

    if auth_code is None:
        return custom_response(False, '授权失败，Auth Code 为空！')

    # 触发换取授权Access Token任务, auth_code, uid
    exchange_authorizer_token.apply_async(args=[auth_code, Master.master_uid()])

    wx_auth_code = WxAuthCode.query.filter_by(auth_code=auth_code).first()
    if wx_auth_code is None:
        # 新增
        wx_auth_code = WxAuthCode(
            master_uid=Master.master_uid(),
            auth_code=auth_code,
            expires_in=expires_in
        )
        db.session.add(wx_auth_code)
    else:
        # 更新
        wx_auth_code.auth_code = auth_code
        wx_auth_code.expires_in = expires_in
        wx_auth_code.created_at = int(timestamp())

    db.session.commit()

    # 授权完成，跳转至设置页
    return redirect('%s?auth_code=%s' % (url_for('main.wxapp_setting'), auth_code))


@open.route('/wx/authorize')
def authorize():
    """跳转授权页"""
    pass


@open.route('/wx/<string:appid>/receive_message')
def receive_message(appid):
    """接收公众号或小程序消息和事件推送"""
    current_app.logger.debug('Appid [%s]' % appid)
    pass
