# -*- coding: utf-8 -*-
from flask import abort, redirect, url_for
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

        # 拒绝访问
        return redirect(url_for('auth.forbidden'))

    return decorator


def user_is_supplier(func, get_user=import_user):
    """装饰器：用户是否为供应商"""

    @wraps(func)
    def decorator(*args, **kwargs):
        current_user = get_user()
        if current_user.id_type == 1:
            return func(*args, **kwargs)

        # 拒绝访问
        return redirect(url_for('auth.forbidden'))

    return decorator


def user_is_distributer(func, get_user=import_user):
    """装饰器：用户是否为分销商"""

    @wraps(func)
    def decorator(*args, **kwargs):
        current_user = get_user()
        if current_user.id_type == 2:
            return func(*args, **kwargs)

        # 拒绝访问
        return redirect(url_for('auth.forbidden'))

    return decorator


def service_has(service, get_user=import_user):
    """装饰器：系统版本是否具有某个服务权限"""

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            from .models import AppService, SubscribeService, EditionService
            desired_service = AppService.query.filter_by(name=service).first()
            if not desired_service:
                return redirect(url_for('auth.forbidden'))

            current_user = get_user()

            # 检测是否自主订购
            master_uid = current_user.id if current_user.is_master else current_user.master_uid
            subscribe_service = SubscribeService.query.filter_by(master_uid=master_uid,
                                                                 service_id=desired_service.id).first()
            if subscribe_service and subscribe_service.status != -1:  # 存在，并未过期
                return func(*args, **kwargs)

            # 检测版本下是否具有
            edition_services = EditionService.services(current_user.edition)
            if desired_service in edition_services:
                return func(*args, **kwargs)

            return redirect(url_for('auth.forbidden'))
        return inner
    return wrapper
