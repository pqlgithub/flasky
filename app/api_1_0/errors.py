# -*- coding: utf-8 -*-
from flask import jsonify
from app.exceptions import ValidationError

from . import api
from .utils import *


@api.errorhandler(400)
def bad_request(e):
	return status_response({
		'code': 400,
		'message': 'Bad request'
	}, False)


@api.errorhandler(401)
def unauthorized(e):
	return status_response({
		'code': 401,
		'message': 'Unauthorized'
	}, False)


@api.errorhandler(403)
def forbidden(e):
	return status_response({
		'code': 403,
		'message': 'Forbidden'
	}, False)


@api.errorhandler(404)
def not_found(e):
	return status_response({
		'code': 404,
		'message': 'Not Found'
	}, False)


@api.errorhandler(ValidationError)
def validation_error(e):
	return status_response({
		'code': e.status_code,
		'message': e.message
	}, False)

