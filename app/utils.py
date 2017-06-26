# -*- coding: utf-8 -*-
import enum, time, random
from flask import jsonify

R200_OK = { 'code': 200, 'message': 'Ok all right.' }
R201_CREATED = { 'code': 201, 'message': 'All created.' }
R204_NOCONTENT = { 'code': 204, 'message': 'All deleted.' }
R400_BADREQUEST = { 'code': 400, 'message': 'Bad request.' }
R403_FORBIDDEN = { 'code': 403, 'message': 'You can not do this.' }
R404_NOTFOUND = { 'code': 404, 'message': 'No result matched.' }
R500_BADREQUEST = { 'code': 500, 'message': 'Request failed.' }

def timestamp():
    '''return the current timestamp as an integer.'''
    return time.time()

def gen_serial_no(prefix='1'):
    """生成产品编号"""
    serial_no = prefix
    serial_no += time.strftime('%y%d')
    # 生成随机数5位
    rd = str(random.randint(1, 1000000))
    z = ''
    if len(rd) < 7:
        for i in range(7-len(rd)):
            z += '0'

    return ''.join([serial_no, z, rd])

def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def full_response(success=True, status=R200_OK, data=None):
    '''结果响应：带数据和状态信息'''
    return jsonify({
        'success': success,
        'status': status,
        'data': data
    })


def status_response(success=True, status=R200_OK):
    '''结果响应：状态信息'''
    return jsonify({
        'success': success,
        'status': status
    })


def custom_status(message, code=400):
    return {
        'code': code,
        'message': message
    }


class DBEnum(enum.Enum):

    @classmethod
    def get_enum_labels(cls):
        return [i.value for i in cls]