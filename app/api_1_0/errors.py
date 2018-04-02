# -*- coding: utf-8 -*-
from flask import jsonify
from .exceptions import ApiError

from . import api
from .utils import *


@api.errorhandler(ApiError)
def handle_api_error(error):
    """添加Api自定义错误码"""
    # response的json内容为自定义错误代码和错误信息
    rv = error.to_dict()
    # response返回error 发生时定义的标准错误代码
    status_code = error.status_code

    return status_response({
        'code': rv.return_code,
        'message': rv.message
    }, False)


@api.errorhandler(400)
def bad_request(e):
    return status_response({
        'code': 400,
        'message': 'Bad request'
    }, False)


@api.errorhandler(404)
def not_found(e):
    return status_response({
        'code': 404,
        'message': 'Not Found'
    }, False)


@api.errorhandler(403)
def forbidden(e):
    return status_response({
        'code': 403,
        'message': 'Forbidden'
    }, False)


@api.errorhandler(401)
def unauthorized(e):
    return status_response({
        'code': 401,
        'message': 'Unauthorized'
    }, False)

