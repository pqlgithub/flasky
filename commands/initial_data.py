# -*- coding: utf-8 -*-

import sys
from flask import current_app
from flask_script import Command
from app import db
from app.constant import DEFAULT_ACLIST, DEFAULT_DIRECTORY, DEFAULT_ASSET, DEFAULT_SUPPLIER, DEFAULT_EXPRESS
from app.models import Ability, Directory, Asset, Express, Supplier, User


class InitialData(Command):
    """Install initial data of system"""

    def run(self):
        print('Initial system data!')

        # 初始化系统用户
        self.init_admin()

        # 安装权限列表
        self.init_acl()

        # 初始化默认目录
        self.init_directory()

        # 初始化默认附件
        self.init_asset()

        # 初始化默认供应商
        self.init_supplier()

        # 初始化默认物流
        self.init_express()

        sys.exit(0)


    def init_admin(self):
        """初始化系统管理员"""
        for email in current_app.config['ADMINS']:
            if User.query.filter_by(email=email,is_admin=True).first():
                print('System user: %s already initial, exit!' % email)

                continue

            user = User(
                email = email,
                username = email.split('@')[0],
                password = 'Mic#2009?!',
                time_zone = 'zh',
                confirmed = True,
                is_admin = True
            )
            db.session.add(user)

        db.session.commit()

        print('System user is initial!')

        return True


    def init_acl(self):

        # 检测是否已安装数据
        total_count = Ability.query.count()
        if total_count:
            print('Ability is initial, exit!')
            return None

        # 安装权限列表
        for acl in DEFAULT_ACLIST:
            ability = Ability(
                name=acl[0],
                title=acl[1]
            )
            db.session.add(ability)

        db.session.commit()


    def init_directory(self):
        """初始化默认目录"""

        default_name = DEFAULT_DIRECTORY['name']
        if Directory.query.filter_by(is_default=True).first():
            print('Default directory already initial, exit!')
            return None

        default_directory = Directory(
            name = default_name,
            is_default = True
        )
        db.session.add(default_directory)
        db.session.commit()

        print('Default directory is initial!')

        return True


    def init_asset(self):
        """初始化附件图片"""

        if Asset.query.filter_by(is_default=True).first():
            print('Default asset already initial, exit!')
            return None

        default_directory = Directory.query.filter_by(is_default=True).first()
        default_asset = Asset(directory=default_directory, **DEFAULT_ASSET)

        db.session.add(default_asset)
        db.session.commit()

        print('Default asset is initial!')

        return True


    def init_supplier(self):
        """初始化默认供应商"""

        if Supplier.query.filter_by(is_default=True).first():
            print('Default supplier already initial, exit!')
            return None

        default_supplier = Supplier(
            **DEFAULT_SUPPLIER
        )

        db.session.add(default_supplier)
        db.session.commit()

        print('Default supplier is initial!')

        return True


    def init_express(self):
        """初始化默认物流公司"""

        if Express.query.filter_by(is_default=True).first():
            print('Default express already initial, exit!')
            return None

        default_express = Express(**DEFAULT_EXPRESS)

        db.session.add(default_express)
        db.session.commit()

        print('Default express is initial!')

        return True






