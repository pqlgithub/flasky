# -*- coding: utf-8 -*-
from flask import g, request, abort
from flask_httpauth import HTTPBasicAuth
from app.models import User, AnonymousUser, Client
from .errors import forbidden, unauthorized
from .decorators import api_sign_required

from .. import db
from . import api
from .utils import *

auth = HTTPBasicAuth()

@api.before_request
@api_sign_required  # 拦截所有请求，进行签名验证
def before_request():
	if not g.master_uid:
		forbidden('App Key is dangerous!')


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
		g.token_used = False # False, 未使用token认证
		
	g.current_user = user
	
	return True


@auth.error_handler
def auth_error():
	"""Return a 401 error to the client."""
	return status_response(R401_AUTHORIZED, False)


@api.route('/auth/register', methods=['POST'])
def register():
	"""用户注册"""
	email = request.json.get('email')
	username = request.json.get('username')
	password = request.json.get('password')
	
	if email is None or password is None or username is None:
		abort(400)
	
	# 验证账号是否存在
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
	

@api.route('/auth/login', methods=['POST'])
def login():
	"""用户登录"""
	pass


@api.route('/auth/logout', methods=['POST'])
def logout():
	"""安全退出"""
	pass


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



