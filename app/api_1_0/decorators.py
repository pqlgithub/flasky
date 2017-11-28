# -*- coding: utf-8 -*-
from functools import wraps
from flask import request, abort, g

from app.models import Client


def api_sign_required(func):
    """装饰器：验证API数字签名"""
    @wraps(func)
    
    def validate_api_sign(*args, **kwargs):
        if request.method == 'GET':
            sign_args = request.args
        else:
            sign_args = request.json
        
        app_key = sign_args.get('app_key')
        # 验证请求参数
        for key in ['app_key', 'timestamp', 'nonce_str', 'sign']:
            if key not in sign_args.keys():
                abort(401)
        
        # 验证是否有app_key
        client = Client.query.filter_by(app_key=app_key).first()
        if client and Client.check_api_sign(sign_args, client.app_secret):
            # 获取当前客户标识ID
            g.master_uid = client.master_uid
            return func(*args, **kwargs)
        else:
            abort(401)
            
    return validate_api_sign