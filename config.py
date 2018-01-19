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

    UPLOADED_PHOTOS_DEST = basedir + '/public/uploads'
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # csrf protected
    WTF_CSRF_ENABLED = True

    # Whoose Index of Full Text Search
    WHOOSH_BASE = basedir + '/whooses'
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

    # 缓存类型
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = '6379'
    CACHE_REDIS_PASSWORD = 'Fr%bird@201403$01'
    CACHE_REDIS_DB = '0'
    
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
    
    # 微信支付
    WECHAT_M_TOKEN = ''
    # 微信APP ID：绑定支付的APP ID（必须配置，开户邮件中可查看）
    WECHAT_M_APP_ID = 'wx08a55a284c50442e'
    # 微信APP SECRET：公众帐号secret
    WECHAT_M_APP_SECRET = '85e685889332e9d69a6268fdec18b92e'
    # 微信MCH ID：商户号
    WECHAT_M_PARTNER_ID = '1305635501'
    # KEY：商户支付密钥
    WECHAT_M_KEY = 'ArioxptbBJu25ANvabeBqavpE7diWUfTtDu1FCkt66Ojdzb1N3ajKoGAX3xdT3GIsj7C8g1pglSBVqaUNrqsoz5vfiASYrinEL4bAvuhTBgs1ZrdX7gJNgx8qgHBG0V4'
    # 异步通知url
    WECHAT_M_NOTIFY_URL = '/wxpay/notify'
    # 设置商户证书路径
    WECHAT_M_SSL_CERT_PATH = '/Users/xiaoyi/Project/micku/wechat_m_cert/apiclient_cert.pem'
    WECHAT_M_SSL_KEY_PATH = '/Users/xiaoyi/Project/micku/wechat_m_cert/apiclient_key.pem'
    WECHAT_M_ROOT_CA = '/Users/xiaoyi/Project/micku/wechat_m_cert/rootca.pem'
    # 设置代理机器，只有需要代理的时候才设置，不需要代理，请设置为0.0.0.0和0
    WECHAT_M_PROXY_HOST = '0.0.0.0'
    WECHAT_M_PROXY_POST = 0
    # 接口调用上报等级，默认紧错误上报（注意：上报超时间为【1s】，上报无论成败【永不抛出异常】
    WECHAT_M_REPORT_LEVEL = 1
    

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    # 缓存类型
    CACHE_TYPE = 'simple'
    
    # Examples: mysql+pymysql://<username>:<password>@<host>/<dbname>[?<options>]
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Urk426#Db10@localhost/mixshopy'
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mixadmin:Mix2009SaaS?@mixsaas.ca1liur05ige.ap-southeast-1.rds.amazonaws.com/MixSaaS?charset=utf8'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Urk426#Db10@localhost/micku_test'


class ProductionConfig(Config):
    MODE = 'prod'

    DEBUG_LOG = False
    DEBUG = False

    # 缓存类型 redis
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = '6379'
    CACHE_REDIS_PASSWORD = ''
    CACHE_REDIS_DB = '0'
    
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


class LllConfig(Config):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/micku_test'

     # Redis 配置
    REDIS_URL = 'redis://localhost:6379/0'

     # Celery Options
    CELERY_IMPORTS = (
        'app.tasks'
    )
    CELERYD_CONCURRENCY = 2
    CELERY_BROKER_URL = 'redis://localhost:6379/5'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/6'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'llh': LllConfig,
}