# -*- coding: utf-8 -*-
"""
    __init__.py
    ~~~~~~~~~~~~~~
    :copyright: (c) 2017 by mix.
"""
from flask import Flask
# 导入扩展
from .extensions import (
    db,
    s3,
    mail,
    csrf,
    pjax,
    babel,
    cache,
    fsk_celery,
    moment,
    bootstrap,
    login_manager
)
# 全文检索
import flask_whooshalchemyplus as whooshalchemyplus
# 导入上传
from flask_uploads import UploadSet, configure_uploads, patch_request_class
# import redis
from .assets import assets_env, bundles
# 导入配置参数
from config import config
from .momentjs import Momentjs


# 创建set
uploader = UploadSet(
    'photos',
    extensions=('xls', 'xlsx', 'jpg', 'jpe', 'jpeg', 'png', 'gif', 'csv')
)
# 属性可以设为None、'basic' 或'strong'
login_manager.session_protection = 'strong'
# 设置登录页面的端点
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # app.redis = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
    #                        db=app.config['REDIS_DB'], password=app.config['REDIS_PASSWORD'])
    # phone_number = current_app.redis.get('token:%s' % token)
    db.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    babel.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    whooshalchemyplus.init_app(app)

    assets_env.init_app(app)
    assets_env.register(bundles)
    s3.init_app(app)
    # 缓存
    cache.init_app(app)
    pjax.init_app(app)

    # Init the Flask-Celery-Helper via app object
    # Register the celery object into app object
    fsk_celery.init_app(app)

    # 初始化上传
    configure_uploads(app, uploader)
    # 文件大小限制，默认为16MB
    patch_request_class(app)

    # logging setting
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(app.config['ERROR_LOG'])
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Mix startup')

    # attach routes

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .adminlte import adminlte as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/adminlte')

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')
    # 禁用csrf
    csrf.exempt(api_1_0_blueprint)

    from .main.filters import timestamp2string, short_filename, supress_none, break_line
    app.add_template_filter(timestamp2string, 'timestamp2string')
    app.add_template_filter(short_filename, 'short_filename')
    app.add_template_filter(supress_none, 'supress_none')
    app.add_template_filter(break_line, 'break_line')

    # Jinja2 导入我们的类作为所有模板的一个全局变量
    app.jinja_env.globals['momentjs'] = Momentjs

    return app
