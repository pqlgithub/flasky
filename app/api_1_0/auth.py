# -*- coding: utf-8 -*-
import time
from flask import g, request, abort, current_app
from flask_httpauth import HTTPBasicAuth
from sqlalchemy.exc import IntegrityError
from app.models import User, AnonymousUser, Client, UserIdType, Store

from .. import db
from . import api
from .utils import *

auth = HTTPBasicAuth()


@auth.error_handler
def auth_error():
    """Return a 401 error to the client."""
    return status_response(R401_AUTHORIZED, False)


@auth.verify_password
def verify_password(email_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(email_or_token)
    g.token_used = True
    if not user:
        # try to authenticate with email/password
        user = User.query.filter_by(email=email_or_token).first()
        if not user or not user.verify_password(password):
            return False
        g.token_used = False  # False, 未使用token认证

    g.current_user = user

    return True


@api.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
    email = request.json.get('email')
    username = request.json.get('username')
    password = request.json.get('password')

    if email is None or password is None or username is None:
        return custom_response('Params is error!', 400, False)

    # 验证账号是否存在
    if User.query.filter_by(email=email).first() is not None:
        return status_response(custom_status('Email already exist!', 400), False)

    # 验证用户名是否唯一
    if User.query.filter_by(username=username).first() is not None:
        return status_response(custom_status('Username already exist!', 400), False)

    try:
        # 添加用户
        user = User()

        user.email = email
        user.username = username
        user.password = password
        user.time_zone = 'zh'
        user.id_type = UserIdType.BUYER

        db.session.add(user)

        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Register user fail: {}'.format(str(err)))

        db.session.rollback()

        return status_response(custom_status('Register failed!', 400), False)

    return status_response(R201_CREATED)


@api.route('/auth/login', methods=['POST'])
@auth.login_required
def login():
    """用户登录"""
    if g.token_used:
        return custom_response('Email or Password is error!', 400, False)

    # 默认： 30天, 30*24*60*60 = 2592000 秒
    expired_time = 2592000

    data = {
        'token': g.current_user.generate_auth_token(expiration=expired_time),
        'expiration': expired_time,
        'created_at': int(time.time())
    }

    return full_response(R200_OK, data)


@api.route('/auth/business_login', methods=['POST'])
@auth.login_required
def business_login():
    """商家登录"""
    if g.token_used:
        return custom_response('Email or Password is error!', 400, False)

    # 默认： 30天, 30*24*60*60 = 2592000 秒
    expired_time = 2592000

    data = {
        'token': g.current_user.generate_auth_token(expiration=expired_time),
        'expiration': expired_time,
        'created_at': int(time.time())
    }

    # 返回店铺信息
    if g.current_user.id_type != UserIdType.SUPPLIER:
        return custom_response('该账号不是商家登录账号', 403, False)

    # 1、登录账号为主账号
    if g.current_user.master_uid == 0:
        # 返回该账号下所有店铺, 如果只有一个店铺，则直接返回该店铺
        stores = Store.query.filter_by(master_uid=g.master_uid).all()
        if len(stores) == 1:
            data['store_rid'] = stores[0].serial_no
        else:
            data['stores'] = [store.to_json() for store in stores]

    # 2、登录账号为子账号
    if g.current_user.master_uid != 0:
        if not g.current_user.store_id:
            return custom_response('该账号没有关联的店铺', 403, False)

        store = Store.query.get(g.current_user.store_id)
        if store is None:
            return custom_response('该账号没有关联的店铺', 403, False)
        data['store_rid'] = store.serial_no

    return full_response(R200_OK, data)


@api.route('/auth/exchange_token', methods=['POST'])
@auth.login_required
def exchange_token():
    """换取商家授权Token"""
    store_rid = request.json.get('store_rid')
    if not store_rid:
        return custom_response('参数不足', 400, False)

    store = Store.query.filter_by(master_uid=g.master_uid, serial_no=store_rid).first()
    if store is None:
        return custom_response('店铺不存在', 404, False)

    client = Client.query.filter_by(master_uid=g.master_uid, store_id=store.id).first()
    if client is None:
        return custom_response('店铺未设置授权信息', 404, False)

    return full_response(R200_OK, {
        'app_key': client.app_key,
        'access_token': client.app_secret
    })


@api.route('/auth/logout', methods=['POST'])
def logout():
    """安全退出"""
    return custom_response('Logout', 401)


@api.route('/auth/find_pwd', methods=['POST'])
def find_pwd():
    """忘记密码"""
    pass


@api.route('/auth/modify_pwd', methods=['POST'])
def modify_pwd():
    """更新密码"""
    pass


@api.route('/auth/verify_code', methods=['POST'])
def verify_code():
    """发送验证码"""
    pass



