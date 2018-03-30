# -*- coding: utf-8 -*-
from flask import render_template,g
from flask_login import login_required, current_user, login_manager

from . import distribute
from ..decorators import user_is_distributer


# 使用before_request修饰器
@distribute.before_request
@login_required
@user_is_distributer
def before_request():
    """
    所有请求前执行
    """
    #  验证是否为分销商身份
    g.user = current_user
    g.current_site = None


@distribute.route('/')
def index():
    """分销后台首页"""

    return render_template('distribute/index.html')
