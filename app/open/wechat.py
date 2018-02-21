# -*- coding: utf-8 -*-
from flask import g, current_app, request, redirect, url_for
import xml.etree.cElementTree as ET

from app.helpers import WXBizMsgCrypt
from . import open


@open.route('/wx/authorize')
def authorize():
    """跳转授权页"""
    pass


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
        app_id = xml_tree.find('AppId').text
        create_time = xml_tree.find('CreateTime').text
        verify_ticket = xml_tree.find('ComponentVerifyTicket').text
        info_type = xml_tree.find('InfoType').text

        current_app.logger.warn('Component verify ticket: %s' % verify_ticket)
    else:
        current_app.logger.warn('error code: %d' % ret)

    return 'success'


@open.route('/wx/<string:appid>/receive_message')
def receive_message(appid):
    """接收公众号或小程序消息和事件推送"""
    pass
