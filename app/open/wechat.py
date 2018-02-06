# -*- coding: utf-8 -*-
from flask import g, current_app, request, redirect, url_for

from . import open


@open.route('/wechat/authorize')
def authorize():
	"""跳转授权页"""
	pass


@open.route('/wechat/authorize_notify')
def authorize_notify():
    """接收取消授权通知、授权成功通知、授权更新通知"""
    pass


@open.route('/wechat/receive_message')
def receive_message():
    """接收公众号或小程序消息和事件推送"""
    pass

