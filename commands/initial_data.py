# -*- coding: utf-8 -*-

import sys
from flask_script import Command
from app.helpers import InitialSystem


class InitialData(Command):
    """
    Install initial data of system
    """

    def run(self):
        print('Initial system data!')

        # 初始化系统用户
		InitialSystem.init_admin()

        # 安装权限列表
		InitialSystem.init_acl()

        # 初始化默认目录
		InitialSystem.init_directory()

        # 初始化默认附件
		InitialSystem.init_asset()

        # 初始化默认供应商
		InitialSystem.init_supplier()

        # 初始化默认物流
		InitialSystem.init_express()

        # 初始化默认币种
		InitialSystem.init_currency()

        sys.exit(0)
