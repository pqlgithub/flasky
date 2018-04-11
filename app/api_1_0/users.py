# -*- coding: utf-8 -*-
from flask import request, abort, g
from app.models import User

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/users/clerks')
def get_clerks():
    """获取某个店铺的全部店员"""
    store_rid = request.values.get('store_rid')



@api.route('/users', methods=['POST'])
def new_user():
    """创建新用户"""
    email = request.json.get('email')
    username = request.json.get('username')
    password = request.json.get('password')
    
    if email is None or password is None:
        abort(400)
        
    if User.query.filter_by(email=email).first() is not None:
        abort(400)
    
    # 添加用户
    user = User()
    
    user.email = email
    user.username = username
    user.password = password
    user.time_zone = 'zh'
    user.id_type = 9
    
    db.session.add(user)
    db.session.commit()
    
    return status_response(R201_CREATED)


@api.route('/users')
@auth.login_required
def get_user():
    """获取当前用户信息"""
    return full_response(R200_OK, g.current_user.to_json())


@api.route('/users', methods=['PUT'])
@auth.login_required
def update_user():
    """更新用户信息"""
    username = request.json.get('username', g.current_user.username)
    name = request.json.get('name', g.current_user.name)
    about_me = request.json.get('about_me', g.current_user.about_me)
    mobile = request.json.get('mobile', g.current_user.mobile)
    description = request.json.get('description',  g.current_user.description)
    
    # 验证username是否存在
    if username and User.query.filter_by(username=username).first():
        return status_response(custom_status('{} already existed!'.format(username), 400), False)
    
    g.current_user.username = username
    g.current_user.name = name
    g.current_user.about_me = about_me
    g.current_user.mobile = mobile
    g.current_user.description = description
    
    db.session.commit()
    
    return full_response(R200_OK, g.current_user.to_json())