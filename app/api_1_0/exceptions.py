# -*- coding: utf-8 -*-
from flask import current_app
from .constant import *


class ApiError(Exception):
    """"API接口异常错误"""

    # 默认错误码
    status_code = 400

    # 自定义一个return_code, 作为更细粒的错误代码
    def __init__(self, return_code=None, status_code=None, payload=None):
        Exception.__init__(self)
        self.return_code = return_code
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    # 构造要返回的错误代码和错误信息的dict
    def to_dict(self):
        rv = dict(self.payload or ())

        rv['return_code'] = self.return_code

        rv['message'] = FX_MSG[self.return_code]

        current_app.logger.warn(FX_MSG[self.return_code])

        return rv
