# -*- coding: utf-8 -*-
from flask import g, current_app, request, redirect, url_for

from app.helpers import WXBizMsgCrypt
from . import open


@open.route('/wx/authorize')
def authorize():
    """跳转授权页"""
    pass


@open.route('/wx/authorize_notify', methods=['GET', 'POST'])
def authorize_notify():
    """接收取消授权通知、授权成功通知、授权更新通知"""
    current_app.logger.warn(request.values)

    signature = request.values.get('signature')
    encrypt_type = request.values.get('encrypt_type')
    timestamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')
    msg_signature = request.values.get('msg_signature')

    post_data = request.get_data()

    current_app.logger.warn(post_data)

    # 解密接口
    des_key = current_app.config['WX_APP_DES_KEY']
    token = current_app.config['WX_APP_TOKEN']
    app_id = current_app.config['WX_APP_ID']

    decrypt = WXBizMsgCrypt(token, des_key, app_id)
    ret, decrypt_content = decrypt.DecryptMsg(post_data, msg_signature, timestamp, nonce)
    # 解密成功
    if ret == 0:
        # 更新ticket
        pass
    current_app.logger.warn("decrypt content: %s" % decrypt_content)

    return 'success'


@open.route('/wx/<string:appid>/receive_message')
def receive_message(appid):
    """接收公众号或小程序消息和事件推送"""
    pass
