# -*- coding: utf-8 -*-
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from app.models import User, AnonymousUser, Client
from .errors import forbidden, unauthorized
from .decorators import api_sign_required
from . import api

auth = HTTPBasicAuth()

@api.before_request
@api_sign_required
def before_request():
	if not g.current_user.is_anonymous and \
		not g.current_user.confirmed:
		return forbidden('Unconfirmed account')


# 生成认证令牌
@api.route('/token')
def get_token():
	if g.current_user.is_anonymous or g.token_used:
		return unauthorized('Invalid credentials')
	return jsonify({'token': g.current_user.generate_auth_token(expiration=3600),
					'expiration': 3600})

@auth.verify_password
def verify_password(email_or_token, password):
	if email_or_token == '':
		g.current_user = AnonymousUser()
		return True
	if password == '': # password为空，代表token认证方式
		g.current_user = User.verify_auth_token(email_or_token)
		g.token_used = True
		return g.current_user is not None
	user = User.query.filter_by(email=email_or_token).first()
	if not user:
		return False
	g.current_user = user
	g.token_used = False # False, 未使用token认证
	return user.verify_password(password)


@auth.error_handler
def auth_error():
	return unauthorized('Invalid credentials')