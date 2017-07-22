# -*- coding: utf-8 -*-
import enum, time, random
from datetime import datetime
from flask import jsonify, current_app
from flask_login import current_user

R200_OK = { 'code': 200, 'message': 'Ok all right.' }
R201_CREATED = { 'code': 201, 'message': 'All created.' }
R204_NOCONTENT = { 'code': 204, 'message': 'All deleted.' }
R400_BADREQUEST = { 'code': 400, 'message': 'Bad request.' }
R403_FORBIDDEN = { 'code': 403, 'message': 'You can not do this.' }
R404_NOTFOUND = { 'code': 404, 'message': 'No result matched.' }
R500_BADREQUEST = { 'code': 500, 'message': 'Request failed.' }



class Master:
    """支持多账户管理，根据当前登录用户返回主账号"""

    @staticmethod
    def master_uid():
        """获取管理员ID"""
        if current_user.is_master:
            return current_user.id
        else:
            return current_user.master_uid if current_user else None

class DBEnum(enum.Enum):

    @classmethod
    def get_enum_labels(cls):
        return [i.value for i in cls]

def create_db_session():
    # create a new session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    psql_url = current_app.config['SQLALCHEMY_DATABASE_URI']
    some_engine = create_engine(psql_url)

    # create a configured 'Session' class
    session = scoped_session(sessionmaker(bind=some_engine))

    return session


def timestamp():
    """return the current timestamp as an integer."""
    return time.time()


def string_to_timestamp(str_value):
    """字符串日期时间转换成时间戳"""
    d = datetime.strptime(str_value, "%Y-%m-%d %H:%M:%S.%f")
    t = d.timetuple()
    timestamp = int(time.mktime(t))
    timestamp = float(str(timestamp) + str("%06d" % d.microsecond)) / 1000000

    return timestamp


def datestr_to_timestamp(str_value):
    """字符串日期转换成时间戳"""
    dt = datetime.strptime(str_value, "%Y-%m-%d")
    return time.mktime(dt.timetuple())


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
    """结果响应：带数据和状态信息"""
    return jsonify({
        'success': success,
        'status': status,
        'data': data
    })


def status_response(success=True, status=R200_OK):
    """结果响应：状态信息"""
    return jsonify({
        'success': success,
        'status': status
    })


def custom_response(success=True, message=None):
    """自定义响应结果"""
    return status_response(success, custom_status(message))


def custom_status(message, code=400):
    return {
        'code': code,
        'message': message
    }


