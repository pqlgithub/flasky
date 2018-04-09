# -*- coding: utf-8 -*-
from flask import jsonify, g, current_app

R200_OK = {'code': 200, 'message': 'Ok all right.'}
R201_CREATED = {'code': 201, 'message': 'All created.'}
R204_NOCONTENT = {'code': 204, 'message': 'All deleted.'}
R400_BADREQUEST = {'code': 400, 'message': 'Bad request.'}
R401_AUTHORIZED = {'code': 401, 'message': 'Unauthorized access.'}
R403_FORBIDDEN = {'code': 403, 'message': 'You can not do this.'}
R404_NOTFOUND = {'code': 404, 'message': 'No result matched.'}


def full_response(status, data, success=True):
    """
    结果响应：带数据和状态信息
    """
    return jsonify({
        'data': data,
        'status': status,
        'success': success
    })


def status_response(status, success=True):
    """
    结果响应：状态信息
    """
    return jsonify({
        'status': status,
        'success': success
    })


def custom_response(message, code=200, success=True):
    """
    结果响应：状态信息
    """
    return jsonify({
        'status': custom_status(message, code),
        'success': success
    })


def custom_status(message, code=200):
    """
    自定义状态信息
    """
    return {
        'code': code,
        'message': message
    }


def can_admin(uid):
    """是否具有管理的权限"""
    # 1、自身为主账号
    if g.current_user.is_master:
        return g.current_user.id == uid

    # 2、自身为子账号
    return g.current_user.master_uid == uid


def is_owner(uid):
    """是否为属主"""
    return g.current_user.id == uid


def correct_int(param):
    """整数型类型转换"""
    if param is None or param == '':
        param = 0
    else:
        param = int(param)

    return param


def correct_str(param):
    """字符串类型转换"""
    if param is None:
        param = ''
    else:
        param = str(param)

    return param


def correct_page(page):
    """修正参数"""
    if page is None or page <= 0:
        page = 1

    return page


def correct_per_page(per_page):
    """修正每页数量"""
    if per_page is None or per_page <= 0:
        per_page = 1

    # 设置最大值
    if per_page > current_app.config['MAX_PER_PAGE']:
        per_page = current_app.config['MAX_PER_PAGE']

    return per_page

