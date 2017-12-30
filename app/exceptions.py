# -*- coding: utf-8 -*-
from flask import current_app


class ValidationError(ValueError):
    
    # 默认错误码
    status_code = 400
    
    # 自定义return_code,更精细化错误码
    def __init__(self, message=None, status_code=None, payload=None):
        ValueError.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        
    def to_dict(self):
        """构造返回的错误代码和错误信息"""
        rv = dict(self.payload or ())
        
        # 增加 message
        rv['message'] = self.message
        
        rv['status_code'] = self.status_code
        
        # 输出日志
        current_app.logger.warn(rv['message'])
        
        return rv
