# -*- coding: utf-8 -*-
from flask import g, session, current_app, request, redirect, url_for
from . import main
from .. import db, babel, cache
from ..utils import make_cache_key


@main.route('/demo')
@cache.cached(timeout=60) # 单位：秒
def cache_demo():
    pass


# 不是仅有视图函数才可以缓存，任何函数都可以
# 只需简单地把装饰器加在函数定义之前。
# key_prefix 对于非视图函数是必须的，并保持唯一
@cache.cached(timeout=7200, key_prefix='sidebar_data')
def cache_custom_function():
    pass


# 缓存带参数的函数
@cache.memoize(60)
def verify_code(c):
    pass


# 缓存带有查询参数的路径
@main.route('/post/<int:post_id>', methods=('GET', 'POST'))
@cache.cached(timeout=600, key_prefix=make_cache_key)
def post(post_id):
    pass

