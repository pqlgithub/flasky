# -*- coding: utf-8 -*-
from flask import redirect, url_for, current_app, render_template
from flask_login import login_required
from . import adminlte
from .. import db
from ..decorators import super_user_required


@adminlte.before_request
@login_required
@super_user_required
def before_request():
    pass


@adminlte.route('/')
def admin_index():
    """管理首页"""
    return redirect(url_for('.show_users'))

