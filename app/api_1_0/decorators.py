# -*- coding: utf-8 -*-
from functools import wraps
from flask import request, abort

from app.models import Client


def api_sign_required(func):
    """装饰器：验证API数字签名"""
    @wraps(func)
    
    def validate_api_sign(*args, **kwargs):
        app_key = request.values.get('app_key')
        # 验证请求参数
        for key in ['app_key', 'timestamp', 'nonce_str', 'sign']:
            if key not in request.values.keys():
                abort(401)
        
        # 验证是否有app_key
        client = Client.query.filter_by(app_key=app_key).first()
        if client and Client.check_api_sign(request.values, client.app_secret):
            return func(*args, **kwargs)
        else:
            abort(401)
            
    return validate_api_sign