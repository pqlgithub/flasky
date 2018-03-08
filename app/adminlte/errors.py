# -*- coding: utf-8 -*-
from flask import render_template, current_app
from . import adminlte


@adminlte.errorhandler(401)
@adminlte.errorhandler(403)
def error_page(e):
    current_app.logger.warn(e)
    return render_template('adminlte/error.html', error=e)
