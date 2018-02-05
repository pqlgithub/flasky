# -*- coding: utf-8 -*-
from datetime import timedelta
from flask import g, session, current_app, request, redirect, url_for, app
from flask_sqlalchemy import get_debug_queries
from flask_login import current_user, login_manager
from . import main
from .. import db, babel
from ..constant import SUPPORT_LANGUAGES
from ..utils import Master, full_response
from app.models import Site, Currency


@babel.localeselector
def get_locale():
    """
    locale selector装饰器
    在请求之前被调用，当产生响应时，选择使用的语言
    """

    # 优先，获取用户设置语言
    user = getattr(g, 'user', None)
    if user is not None and type(user):
        return user.locale

    # 其次，当前选择语言
    current_site = getattr(g, 'current_site', None)
    if current_site is not None:
        return current_site.locale

    # 最后，使用默认语言
    return request.accept_languages.best_match(
        [lang[1].lower() for lang in SUPPORT_LANGUAGES])


@babel.timezoneselector
def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone


# 必须使用before_app_request修饰器
@main.before_request
def before_request():
    """
    Such a function is executed before each request, even if outside of a blueprint.
    """
    g.user = current_user

    # 验证用户
    if current_user.is_authenticated:
        # 每次收到用户的请求时都要调用ping()方法
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))

        # 验证是否设置初始信息
        if not current_user.is_setting:
            if request.path[:8] != '/static/' and request.endpoint[5:] != 'logout' and \
                    request.endpoint[5:17] != 'setting_site':
                return redirect(url_for('main.setting_site'))

        # 注入站点信息
        g.current_site = Site.query.filter_by(
            master_uid=Master.master_uid()).first()
    else:
        g.current_site = None

    # 设置本地化语言
    g.locale = get_locale()


@main.context_processor
def include_init_data():
    """注入共用的变量"""

    return {
        'support_languages': SUPPORT_LANGUAGES,
        'current_site': g.current_site
    }


@main.before_request
def make_session_permanent():
    """请求前执行,为单独请求设立不操作超时机制,每次请求刷新失效时间"""
    session.permanent = True  # 关闭浏览器重新打开还保存session
    app.permanent_session_lifetime = timedelta(minutes=30)  # session失效时间
    login_manager.remember_cookie_duration = timedelta(
        minutes=30)  # cookie失效时间


# 针对程序全局请求的钩子，
@main.after_request
def after_request(response):
    """
    Such a function is executed after each request, even if outside of the blueprint.
    """
    for query in get_debug_queries():
        if query.duration >= current_app.config['DATABASE_QUERY_TIMEOUT']:
            current_app.logger.warn(
                "SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" %
                (query.statement, query.parameters, query.duration, query.context))
    return response


@main.route('/<string:lang>')
def choose_locale(lang):
    """切换语言"""
    lang = lang.lower()
    if lang not in [lang[1].lower() for lang in SUPPORT_LANGUAGES]:
        # 设置默认语言
        lang = current_app.config['BABEL_DEFAULT_LOCALE']

    g.user.locale = lang

    # remove the locale from the session if it's there
    # session.pop('locale', None)

    return redirect(request.args.get('next') or url_for('main.index'))


@main.route('/change_currency')
def change_currency():
    """改变货币单位，自动转换汇率"""
    fc = request.values.get('fc')
    tc = request.values.get('tc')

    from_currency = Currency.query.filter_by(code=fc).first()
    to_currency = Currency.query.filter_by(code=tc).first()

    current_app.logger.debug(
        'Default currency [%d], from [%d], to [%d]' %
        (g.current_site.currency_id, from_currency.id, to_currency.id))

    current_rate = 1.00
    if g.current_site.currency_id == from_currency.id:
        current_rate = current_rate * float(to_currency.value)

    if g.current_site.currency_id == to_currency.id:
        current_rate = current_rate / float(from_currency.value)

    if g.current_site.currency_id != from_currency.id and g.current_site.currency_id != to_currency.id:
        current_rate = (current_rate * float(to_currency.value)
                        ) / float(from_currency.value)

    return full_response(success=True, data={'rate': current_rate})
