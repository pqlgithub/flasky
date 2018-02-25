# -*- coding: utf-8 -*-
# 装载静态文件
from flask_bootstrap import Bootstrap
# 国际化和本地化
from flask_babelex import Babel
# 邮件
from flask_mail import Mail
# 数据库连接
from flask_sqlalchemy import SQLAlchemy
# 本地化日期和时间
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from flask_cdn import CDN
# pjax
from flask_pjax import PJAX
# 管理用户认证系统中的认证状态
from flask_login import LoginManager
# 缓存
from flask_caching import Cache
# 后台定时任务
from flask_celery import Celery


db = SQLAlchemy()
mail = Mail()
pjax = PJAX()
csrf = CSRFProtect()
babel = Babel()
cache = Cache()
# Create the Flask-Celery-Helper's instance
fsk_celery = Celery()
moment = Moment()
bootstrap = Bootstrap()
# Flask-Login初始化
login_manager = LoginManager()
# cdn
cdn = CDN()
