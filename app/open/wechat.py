# -*- coding: utf-8 -*-
from flask import g, current_app, request, redirect, url_for

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
    timestamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')
    encrypt_type = request.values.get('encrypt_type')
    msg_signature = request.values.get('msg_signature')

    post_data = request.get_data()

    current_app.logger.warn(post_data)

    return 'success'


@open.route('/wx/<string:appid>/receive_message')
def receive_message(appid):
    """接收公众号或小程序消息和事件推送"""
    pass
