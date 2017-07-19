# -*- coding: utf-8 -*-
"""
    config.py
    ~~~~~~~~~~~~~~~~~

    Default configuration

    :copyright: (c) 2017 by Mic.
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # change this in your production settings !!!
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
    FLASKS3_BUCKET_NAME = 's3.michose.com'
    FLASKS3_CDN_DOMAIN = 's3.michose.com'
    FLASKS3_FORCE_MIMETYPE = True

    # Asset Bucket
    ASSET_BUCKET_NAME = 'g3.michose.com'
    ASSET_CDN_DOMAIN = 'g3.michose.com'
    THUMB_CDN_DOMAIN = 'img3.michose.com'

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
    DEBUG_LOG = False
    DEBUG = False

    ASSETS_DEBUG = False
    FLASK_ASSETS_USE_S3 = True
    FLASKS3_USE_HTTPS = False
    FLASKS3_CDN_DOMAIN = 's3.michose.com'

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mixadmin:Mix2009SaaS?@prodbmixsaas.ca1liur05ige.ap-southeast-1.rds.amazonaws.com/ProdbMixSaaS?charset=utf8'

    ERROR_LOG = '/var/log/mic-error.log'

    # Whoose Index of Full Text Search
    WHOOSH_BASE = '/opt/project/whoose'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}