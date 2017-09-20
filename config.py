# -*- coding: utf-8 -*-
"""
    config.py
    ~~~~~~~~~~~~~~~~~

    Default configuration

    :copyright: (c) 2017 by Mic.
"""

import os
from datetime import timedelta
from celery.schedules import crontab

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # change this in your production settings !!!

    MODE = 'dev'

    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Mic#2018%0110!'

    # 默认语言, zh_CN,
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'

    DB_PREFIX = 'fp_'
    # 配置输出SQL语句
    SQLALCHEMY_ECHO = True

    # 每次request自动提交db.session.commit()
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # slow database query threshold (in seconds)
    DATABASE_QUERY_TIMEOUT = 0.5

    # 管理员
    ADMINS = ('purpen.w@gmail.com',)

    # 邮件服务
    DEFAULT_MAIL_SENDER = 'support@qq.com'

    MAIL_SERVER = 'stmp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'Admin'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'Mic2018'
    MAIL_SUBJECT_PREFIX = '[MIC]'
    MAIL_SENDER = os.environ.get('MAIL_SENDER') or DEFAULT_MAIL_SENDER

    # Can not compress the CSS/JS on Dev environment.
    IMAGE_SIZE = (480, 480)
    ASSETS_DEBUG = True

    # Use Amazon S3
    FLASK_ASSETS_USE_S3 = False
    FLASKS3_ACTIVE = True
    FLASKS3_USE_HTTPS = False
    FLASKS3_BUCKET_NAME = 's3.mixpus.com'
    FLASKS3_CDN_DOMAIN = 's3.mixpus.com'
    FLASKS3_FORCE_MIMETYPE = True

    # Asset Bucket
    ASSET_BUCKET_NAME = 'g3.michose.com'
    ASSET_CDN_DOMAIN = 'g3.michose.com'
    THUMB_CDN_DOMAIN = 'g3.michose.com'

    AWS_ACCESS_KEY = 'AKIAJMIYNJXL7QEHTXNQ'
    AWS_ACCESS_SECRET = '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'

    # 日志
    ERROR_LOG = 'logs/mic-error.log'

    # pagination
    MAX_SEARCH_RESULTS = 50
    POSTS_PER_PAGE = 50

    # css/js
    # BOOTSTRAP_SERVE_LOCAL = False

    UPLOADED_PHOTOS_DEST = '/Users/xiaoyi/Project/micku/public/uploads'
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # csrf protected
    WTF_CSRF_ENABLED = True

    # Whoose Index of Full Text Search
    WHOOSH_BASE = '/Users/xiaoyi/Project/micku/whooses'
    MAX_SEARCH_RESULTS = 50

    # Pjax base template
    PJAX_BASE_TEMPLATE = 'pjax.html'

    # Redis 配置
    REDIS_URL = 'redis://:Fr%bird@201403$01@localhost:6379/0'

    # Celery Options
    CELERY_IMPORTS = (
        'app.tasks'
    )
    CELERY_BROKER_URL = 'redis://:Fr%bird@201403$01@localhost:6379/5'
    CELERY_RESULT_BACKEND = 'redis://:Fr%bird@201403$01@localhost:6379/6'

    # schedules
    CELERYBEAT_SCHEDULE = {
        #'add-every-30-seconds': {
        #    'task': 'app.tasks.xxx',
        #    # 每 30 秒执行一次
        #    'schedule': timedelta(seconds=30),
        #    'args': (5, 8)
        #},
        'update-today-currency': {
            'task': 'app.tasks.async_currency_rate',
            # 每天上午 11 点 59 分执行一次
            'schedule': crontab(hour=11, minute=59),
            'args': ()
        }
    }

    # Currency API
    CURRENCY_API_CODE = '16122e1e525b4cdb869d538b143fe231'
    CURRENCY_API_HOST = 'http://jisuhuilv.market.alicloudapi.com'
    CURRENCY_API_SINGLE = '/exchange/single'
    CURRENCY_API_CONVERT = '/exchange/convert'
    CURRENCY_API_ALL = '/exchange/currency'


    # 快递鸟
    KDN_APP_ID = '1302778'
    KDN_APP_KEY = '243d245a-4184-48f4-8072-9485de34a705'
    KDN_APP_ROOT_URL = 'http://testapi.kdniao.cc:8081/api'


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    # Examples: mysql+pymysql://<username>:<password>@<host>/<dbname>[?<options>]
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Urk426#Db10@localhost/micku_dev'
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mixadmin:Mix2009SaaS?@mixsaas.ca1liur05ige.ap-southeast-1.rds.amazonaws.com/MixSaaS?charset=utf8'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Urk426#Db10@localhost/micku_test'


class ProductionConfig(Config):
    MODE = 'prod'

    DEBUG_LOG = False
    DEBUG = False

    ASSETS_DEBUG = False
    FLASK_ASSETS_USE_S3 = True
    FLASKS3_USE_HTTPS = False
    FLASKS3_CDN_DOMAIN = 's3.mixpus.com'

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mixadmin:Mix2009SaaS?@prodbmixsaas.ca1liur05ige.ap-southeast-1.rds.amazonaws.com/ProdbMixSaaS?charset=utf8'

    ERROR_LOG = '/var/log/mic-error.log'

    UPLOADED_PHOTOS_DEST = '/opt/project/mishoply/public/uploads'

    # Whoose Index of Full Text Search
    WHOOSH_BASE = '/opt/project/whoose'

    # 快递鸟
    KDN_APP_ROOT_URL = 'http://api.kdniao.cc/api'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}