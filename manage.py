#!venv/bin/python
# -*- coding: utf-8 -*-
import os
from werkzeug.contrib.fixers import ProxyFix
from flask_script import Server, Manager, Shell
from flask_script.commands import ShowUrls, Clean
from flask_migrate import Migrate, MigrateCommand
from flask_assets import ManageAssets
from flask_s3 import create_all

from app import create_app, db
from app.models import User, Role, Order, Product, ProductSku, Purchase
from app.assets import assets_env
from commands.initial_data import InitialData
from commands.fix_data import FixData
from commands.init_summary import InitSummary

# 加载环境变量
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

basedir = os.path.abspath(os.path.dirname(__file__))

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


@manager.command
def upload_files_s3():
    """静态文件同步至S3"""
    create_all(
        app,
        user=app.config['AWS_ACCESS_KEY'],
        password=app.config['AWS_ACCESS_SECRET'],
        bucket_name=app.config['FLASKS3_BUCKET_NAME'],
        location='ap-southeast-1',
        include_hidden=False)


@manager.option('-m', '--model', dest='model', default='all')
def whoose_index(model):
    """手动建立全文索引"""
    from flask_whooshalchemyplus import index_all, index_one_model
    models = {
        'Order': Order,
        'Purchase': Purchase,
        'Product': Product,
        'ProductSku': ProductSku
    }
    if model == 'all':
        index_all(app)
    elif model in models.keys():
        index_one_model(models[model])
    else:
        pass


@manager.command
def test():
    """Run the unit test."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def run_sql():
    sql = "SELECT SUM(s.quantity) FROM `purchase_product` AS s LEFT JOIN `purchases` AS p ON s.purchase_id=p.id"
    sql += " WHERE s.product_sku_id=%d AND p.status=5" % 1023

    result = db.engine.execute(sql).fetchone()

    return result[0] if result[0] is not None else 0


# 常用操作命令
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('show-urls', ShowUrls())
# 清除工作目录中Python编译的.pyc和.pyo文件
manager.add_command('clean', Clean())
# 初始化系统命令
manager.add_command('initial', InitialData())
# 统计数据初始化
manager.add_command('init_summary', InitSummary)
# css/js 静态文件压缩
manager.add_command('assets', ManageAssets(assets_env))
# 修正数据
manager.add_command('fix_data', FixData())

# 启动测试服务器
server = Server(host='0.0.0.0', port=5000)
manager.add_command('server', server)

# 项目的代理设置
app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    manager.run()
