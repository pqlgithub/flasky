# -*- coding: utf-8 -*-
"""
    config.py
    ~~~~~~~~~~~~~~~~~

    Default configuration

    :copyright: (c) 2017 by purpen.
"""

import os
from datetime import timedelta
from celery.schedules import crontab

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # change this in your production settings !!!

    MODE = 'dev'
    DOMAIN_URL = 'http://127.0.0.1:9000'

    CSRF_ENABLED = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Mic#2018%0110!'

    # 默认语言, zh_CN,
    BABEL_DEFAULT_LOCALE = 'zh'
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

    MAIL_SERVER = 'stmp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'Admin'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'Mic2018'
    MAIL_SUBJECT_PREFIX = '[MIC]'
    MAIL_SENDER = os.environ.get('MAIL_SENDER') or DEFAULT_MAIL_SENDER

    # AWS_ACCESS_KEY = 'AKIAJMIYNJXL7QEHTXNQ'
    # AWS_ACCESS_SECRET = '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'

    # Can not compress the CSS/JS on Dev environment.
    IMAGE_SIZE = (480, 480)

    # Asset Bucket
    ASSETS_DEBUG = True
    FLASK_ASSETS_USE_CDN = True
    CDN_DEBUG = True
    CDN_HTTPS = True
    CDN_TIMESTAMP = True
    CDN_ENDPOINTS = ['static']
    CDN_DOMAIN = 'kg.erp.taihuoniao.com'
    THUMB_CDN_DOMAIN = 'kg.erp.taihuoniao.com'

    # 七牛存储（生产环境使用云存储）
    QINIU_UPLOAD = 'https://up.qbox.me'
    QINIU_ACCESS_KEY = 'AWTEpwVNmNcVjsIL-vS1hOabJ0NgIfNDzvTbDb4i'
    QINIU_ACCESS_SECRET = 'F_g7diVuv1X4elNctf3o3bNjhEAe5MR3hoCk7bY6'
    QINIU_BUCKET_NAME = 'frking'

    # 日志
    ERROR_LOG = 'logs/mic-error.log'

    # pagination
    MAX_PER_PAGE = 500
    MAX_SEARCH_RESULTS = 50
    POSTS_PER_PAGE = 50

    # css/js
    # BOOTSTRAP_SERVE_LOCAL = False

    UPLOADED_PHOTOS_DEST = basedir + '/public/uploads'
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'pem', 'p12'])
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # csrf protected
    WTF_CSRF_ENABLED = True

    # Whoose Index of Full Text Search
    WHOOSH_BASE = basedir + '/whooses'

    # Pjax base template
    PJAX_BASE_TEMPLATE = 'pjax.html'

    # Redis 配置
    REDIS_URL = 'redis://:Fr%bird@201403$01@localhost:6379/0'

    # Celery Options
    CELERY_IMPORTS = (
        'app.tasks'
    )
    CELERY_BROKER_URL = 'redis://localhost:6379/5'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/6'

    # schedules
    CELERYBEAT_SCHEDULE = {
        # 每5分钟检测刷新微信token
        'wx-refresh-token': {
            'task': 'wx.refresh_component_token',
            'schedule': timedelta(seconds=300),
            'args': ()
        },
        # 每5分钟检测刷新授权方token
        'wx-refresh-authorizer-token': {
            'task': 'wx.refresh_authorizer_token',
            'schedule': timedelta(seconds=300),
            'args': ()
        },
        # 每天上午 11 点 59 分执行一次
        'update-today-currency': {
            'task': 'app.tasks.async_currency_rate',
            'schedule': crontab(hour=11, minute=59),
            'args': ()
        },
        'every-minute-demo': {
            'task': 'demo.add_together',
            'schedule': timedelta(seconds=60),
            'args': (1, 1)
        }
    }

    # 缓存类型
    # CACHE_REDIS_URL 连接到Redis服务器的URL。
    # 例如：redis://user:password@localhost:6379/2。 仅用于RedisCache。
    CACHE_TYPE = 'redis'
    CACHE_KEY_PREFIX = 'fx_'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = '6379'
    CACHE_REDIS_PASSWORD = ''
    CACHE_REDIS_DB = '2'
    CACHE_REDIS_URL = 'redis://:@localhost:6379/2'

    # Currency API
    CURRENCY_API_CODE = '16122e1e525b4cdb869d538b143fe231'
    CURRENCY_API_HOST = 'http://jisuhuilv.market.alicloudapi.com'
    CURRENCY_API_SINGLE = '/exchange/single'
    CURRENCY_API_CONVERT = '/exchange/convert'
    CURRENCY_API_ALL = '/exchange/currency'

    # 快递鸟
    KDN_APP_ID = '1302778'
    KDN_APP_KEY = '243d245a-4184-48f4-8072-9485de34a705'
    KDN_APP_ROOT_URL = 'http://api.kdniao.cc/api'

    # 小程序第三方开发
    WX_APP_TOKEN = 'AKIAJMIYNJXL7QEHTXNQ'
    WX_APP_DES_KEY = '16122e1e525b4cdb869d538b143fe231d69a6268fb9'
    WX_APP_ID = 'wx80ea263688082055'
    WX_APP_SECRET = 'c37328fc19aec73f471ab761508bba2d'

    # 微信支付
    WXPAY_APP_ID = 'wx11363b7f6fe26ac8'  # 小程序ID
    # 商户号
    WXPAY_MCH_ID = '1490941762'
    # 商户支付密钥
    WXPAY_MCH_SECRET = 'a4a3cae89a6e71338df9ca65c7841c96'
    # 异步通知url
    WXPAY_NOTIFY_URL = '/open/wx/pay_notify'

    # 设置商户证书路径
    WXPAY_SSL_CERT_PATH = '/Users/xiaoyi/Project/micku/wxpay_m_cert/apiclient_cert.pem'
    WXPAY_SSL_KEY_PATH = '/Users/xiaoyi/Project/micku/wxpay_m_cert/apiclient_key.pem'
    WXPAY_ROOT_CA = '/Users/xiaoyi/Project/micku/wxpay_m_cert/rootca.pem'
    # 设置代理机器，只有需要代理的时候才设置，不需要代理，请设置为0.0.0.0和0
    WXPAY_PROXY_HOST = '0.0.0.0'
    WXPAY_PROXY_POST = 0
    # 接口调用上报等级，默认紧错误上报（注意：上报超时间为【1s】，上报无论成败【永不抛出异常】
    WXPAY_REPORT_LEVEL = 1

    # 微信自动化测试的专用测试小程序的信息
    WX_TEST_APP_ID = 'wxd101a85aa106f53e'
    WX_TEST_USERNAME = 'gh_8dad206e9538'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    ASSETS_DEBUG = True
    CDN_DEBUG = True
    CDN_HTTPS = False

    # Examples:
    # mysql+pymysql://<username>:<password>@<host>/<dbname>[?<options>]
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/mixshopy'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Urk426#Db10@localhost/micku_test'


class ProductionConfig(Config):
    MODE = 'prod'
    DOMAIN_URL = 'https://fx.taihuoniao.com'

    DEBUG_LOG = False
    DEBUG = False

    # 缓存类型 redis
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = '0'
    CACHE_REDIS_PASSWORD = ''

    # 静态文件
    ASSETS_DEBUG = False
    CDN_DEBUG = False
    CDN_HTTPS = True

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://fxadmin:fxdb@1801?!@10.10.39.2/fxshopy?charset=utf8'

    ERROR_LOG = '/var/log/fxerp/mix-error.log'

    UPLOADED_PHOTOS_DEST = '/data/fxerp/uploads'

    # Whoose Index of Full Text Search
    WHOOSH_BASE = '/opt/project/whoose'

    # 快递鸟
    KDN_APP_ROOT_URL = 'http://api.kdniao.cc/api'

    # 设置商户证书路径
    WXPAY_SSL_CERT_PATH = '/opt/project/fxerp/wxpay_m_cert/apiclient_cert.pem'
    WXPAY_SSL_KEY_PATH = '/opt/project/fxerp/wxpay_m_cert/apiclient_key.pem'
    WXPAY_ROOT_CA = '/opt/project/fxerp/wxpay_m_cert/rootca.pem'

    # 异步通知url
    WXPAY_NOTIFY_URL = 'https://fx.taihuoniao.com/open/wx/pay_notify'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

conf_name = os.getenv('FLASK_CONFIG') or 'default'
running_config = config[conf_name]
