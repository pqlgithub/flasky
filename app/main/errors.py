# -*- coding: utf-8 -*-
from flask import render_template, request, jsonify

from app.main import main

# 为所有客户端生成适当响应的一种方法是，在错误处理程序中根据客户端请求的格式改写
# 响应，这种技术称为内容协商
@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response

    return render_template('error/404.html'), 404


@main.app_errorhandler(403)
def forbidden(e):
    return render_template('error/403.html'), 403


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'Internal server error'})
        response.status_code = 500
        return response
    return render_template('error/500.html'), 500