# -*- coding: utf-8 -*-
from flask import render_template, current_app
from . import distribute


@distribute.errorhandler(401)
@distribute.errorhandler(403)
@distribute.errorhandler(404)
@distribute.errorhandler(500)
def error_page(e):
    current_app.logger.warn(e.code)

    if e.code == 403:
        errmsg = '权限限制，不允许访问！'
    elif e.code == 401:
        errmsg = '未被授权访问！'
    elif e.code == 404:
        errmsg = '访问资源不存在！'
    else:
        errmsg = str(e)

    return render_template('distribute/errors.html', errmsg=errmsg)
