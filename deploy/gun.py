# -*- coding: utf-8 -*-

import os
import gevent.monkey
import multiprocessing

gevent.monkey.patch_all()

# 监听本机的9000端口
bind = '127.0.0.1:9000'

preload_app = True

# 启动的进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 每个进程的开启线程
threads = multiprocessing.cpu_count() * 2

backlog = 2048

# 工作模式为gevent
workers_class = 'gunicorn.workers.ggevent.GeventWorker'

debug = False

# 如果不使用supervisord之类的进程管理工具可以是进程成为守护进程，否则会出问题
# INFO exited: gunicorn (exit status 0; not expected)
daemon = True

# 进程名称
proc_name = 'gunicorn.pid'
# 进程pid记录文件
pidfile = '/var/run/fxerp/gunicorn.pid'


loglevel = 'debug'
logfile = '/var/log/fxerp/mix.log'
accesslog = '/var/log/fxerp/mix-access.log'
access_log_format = '%(h)s %(t)s %(U)s %(q)s'
errorlog = '/var/log/fxerp/mix-error.log'


x_forwarded_for_header = 'X-FORWARDED-FOR'
