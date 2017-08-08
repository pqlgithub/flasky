#!venv/bin/python
# -*- coding: utf-8 -*-

import os

# 加载环境变量
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from flask_script import Server, Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_apidoc.commands import GenerateApiDoc
from flask_assets import ManageAssets
from flask_s3 import create_all
from werkzeug.contrib.fixers import ProxyFix

from app import create_app, db
from app.models import User, Role
from app.assets import assets_env

from commands.initial_data import InitialData

basedir = os.path.abspath(os.path.dirname(__file__))

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


@manager.command
def upload_files_s3():
    """静态文件同步至S3"""
    create_all(app, user=app.config['AWS_ACCESS_KEY'], password=app.config['AWS_ACCESS_SECRET'],
               bucket_name=app.config['FLASKS3_BUCKET_NAME'], location='ap-southeast-1')


@manager.command
def update_index_all():
    """手动建立索引"""
    from flask_whooshalchemyplus import index_all
    index_all(app)


@manager.command
def test():
    """Run the unit test."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def run_sql():
    sql = "SELECT cp.category_id, group_concat(c.name ORDER BY cp.level SEPARATOR '&nbsp;&nbsp;&gt;&nbsp;&nbsp;'), c2.sort_order, c2.status FROM categories_paths AS cp"
    sql += " LEFT JOIN categories c ON (cp.path_id=c.id)"
    sql += " LEFT JOIN categories AS c2 ON (cp.category_id=c2.id)"

    sql += ' GROUP BY cp.category_id'
    #sql += ' ORDER BY c2.sort_order ASC'

    result = db.engine.execute(sql)

    for row in result:
        print(row)



# 常用操作命令
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

server = Server(host='0.0.0.0', port=9000)
manager.add_command('runserver', server)

# 更新API doc文档
manager.add_command('apidoc', GenerateApiDoc(input_path='app/api_1_0',
                                             output_path='public/docs'))

# css/js 静态文件压缩
manager.add_command('assets', ManageAssets(assets_env))

# 初始化系统命令
manager.add_command('initial', InitialData())

# 项目的代理设置
app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    manager.run()
