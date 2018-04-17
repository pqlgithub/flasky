# -*- coding: utf-8 -*-
from functools import wraps
from flask import request, abort, g, current_app

from app.models import Client, User
from .utils import *


def api_sign_required(func):
    """装饰器：验证API数字签名"""
    @wraps(func)
    def validate_api_sign(*args, **kwargs):
        # 测试环境跳过验证
        if current_app.config['MODE'] == 'dev':
            g.master_uid = 2
            g.store_id = 2
            return func(*args, **kwargs)

        exempt = ['business_login', 'exchange_token']

        # 排除某些请求的签名验证
        paths = request.path.split('/')
        endpoint = paths.pop()
        if endpoint in exempt:
            g.master_uid = 0
            g.store_id = 0
            return func(*args, **kwargs)

        sign_args = request.values if request.values else request.json

        if not sign_args:
            return status_response({
                'code': 601,
                'message': 'Sign parameters is null'
            }, False)

        app_key = sign_args.get('app_key')
        # 验证请求参数
        for key in ['app_key', 'timestamp', 'nonce_str', 'sign']:
            if key not in sign_args.keys():
                return status_response({
                    'code': 601,
                    'message': 'Sign parameters missing'
                }, False)

        # 验证是否有app_key
        client = Client.query.filter_by(app_key=app_key).first()
        if client and Client.check_api_sign(sign_args, client.app_secret):
            # 获取当前客户标识ID
            g.master_uid = client.master_uid
            # 获取关联的渠道ID
            g.store_id = client.store_id
            return func(*args, **kwargs)
        else:
            return status_response({
                'code': 602,
                'message': 'Sign error'
            }, False)
            
    return validate_api_sign


def admin_required(func):
    """管理员权限装饰器"""
    @wraps(func)
    def decorator(*args, **kwargs):
        token_header = request.headers.get('authorization')
        # 去掉格式中的Basic
        token = token_header[6:]
        if token:
            g.current_user = User.verify_auth_token(token)
            if g.current_user.is_adminstractor():
                return func(*args, **kwargs)
            else:
                abort(403)
    
    return decorator
