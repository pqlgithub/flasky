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
    return 'success'


@open.route('/wx/<string:appid>/receive_message')
def receive_message(appid):
    """接收公众号或小程序消息和事件推送"""
    pass
