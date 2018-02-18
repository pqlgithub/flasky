# -*- coding: utf-8 -*-
from flask import g, request, current_app

from .. import db
from . import api
from .utils import full_response, R200_OK
from app.helpers import WxApp


@api.route('/accounts/wxapp_login', methods=['POST'])
def verify_wxapp_login():
    """
    小程序的新用户登录/注册
    1、如用户存在，则返回Token
    2、如用户不存在，则先自动注册，再返回Token
    """
    js_code = request.json.get('code')
    encrypted_data = request.json.get('encrypted_data')
    iv = request.json.get('iv')

    wxapi = WxApp(current_app.config['WX_MINI_APP_ID'], current_app.config['WX_MINI_APP_SECRET'])
    # 1、使用 code 换取 session key
    session_info = wxapi.jscode2session(js_code)

    session_key = session_info.get('session_key')
    # 2、解密得到用户信息

    user_info = wxapi.decrypt(session_key, encrypted_data, iv)

    return full_response(R200_OK, user_info)

