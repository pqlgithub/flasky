# -*- coding: utf-8 -*-
from flask import abort
from functools import wraps
from werkzeug.exceptions import Forbidden


def import_user():
    try:
        from flask_login import current_user
        return current_user
    except ImportError:
        raise ImportError('User argument not passed and Flask-Login current_user could not be imported.')


# 装饰器：用户是否具有某权限
def user_has(ability, get_user=import_user):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            from .models import Ability
            desired_ability = Ability.query.filter_by(name=ability).first()
            user_abilities = []
            current_user = get_user()
            # 主账号，具有全部权限
            if current_user.is_master:
                return func(*args, **kwargs)
            for role in current_user.roles:
                user_abilities += role.abilities
            if desired_ability in user_abilities:
                return func(*args, **kwargs)
            else:
                raise Forbidden('You do not have access')
        return inner
    return wrapper


# 装饰器：用户是否为某角色
def user_is(role, get_user=import_user):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            current_user = get_user()
            # 主账号，具有全部权限
            if current_user.is_master:
                return func(*args, **kwargs)
            if role in current_user.has_roles():
                return func(*args, **kwargs)
            raise Forbidden('You do not have access')
        return inner
    return wrapper


def super_user_required(func, get_user=import_user):
    """装饰器：用户是否为系统管理员"""

    @wraps(func)
    def decorator(*args, **kwargs):
        current_user = get_user()
        if current_user.is_adminstractor():
            return func(*args, **kwargs)
        abort(403)

    return decorator
