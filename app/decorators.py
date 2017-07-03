# -*- coding: utf-8 -*-
from functools import wraps
from werkzeug.exceptions import Forbidden

def import_user():
    try:
        from flask_login import current_user
        return current_user
    except ImportError:
        raise ImportError('User argument not passed and Flask-Login current_user could not be imported.')


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