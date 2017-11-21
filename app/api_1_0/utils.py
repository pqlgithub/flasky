# -*- coding: utf-8 -*-
from flask import jsonify

R200_OK = { 'code': 200, 'message': 'Ok all right.' }
R201_CREATED = { 'code': 201, 'message': 'All created.' }
R204_NOCONTENT = { 'code': 204, 'message': 'All deleted.' }
R400_BADREQUEST = { 'code': 400, 'message': 'Bad request.' }
R403_FORBIDDEN = { 'code': 403, 'message': 'You can not do this.' }
R404_NOTFOUND = { 'code': 404, 'message': 'No result matched.' }

def full_response(status, data):
	"""
	结果响应：带数据和状态信息
	"""
	return jsonify({
		'status': status,
		'data': data
	})

def status_response(status):
	"""
	结果响应：状态信息
	"""
	return jsonify({
		'status': status
	})


def custom_status(message, code=200):
	"""
	自定义状态信息
	"""
	return {
		'code': code,
		'message': message
	}