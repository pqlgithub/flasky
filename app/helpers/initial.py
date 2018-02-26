# -*- coding: utf-8 -*-
from flask import current_app
from app import db
from app.constant import DEFAULT_ACLIST, DEFAULT_DIRECTORY, DEFAULT_ASSET, DEFAULT_SUPPLIER, DEFAULT_EXPRESS, \
    DEFAULT_CURRENCIES
from app.models import User, Ability, Directory, Asset, Supplier, Express, Currency, Country

__all__ = [
    'InitialSite',
    'InitialSystem'
]


class InitialSite(object):
    """
    创建主账号后，需同步添加的默认配置
    """

    @staticmethod
    def install_role(uid=0):
        """自动创建默认用户角色及权限列表"""
        pass

    @staticmethod
    def install_currency(uid=0):
        """初始化默认币种"""

        for data in DEFAULT_CURRENCIES:
            if Currency.query.filter_by(master_uid=uid, code=data['code']).first():
                print('System currency already initial, exit!')
                continue

            data['master_uid'] = uid
            currency = Currency(**data)
            db.session.add(currency)

        db.session.commit()

    @staticmethod
    def install_directory(uid=0):
        """自动创建默认目录"""
        directories = ['fx_default_directory', 'fx_product_directory', 'fx_brand_directory', 'fx_category_directory',
                       'fx_user_directory', 'fx_advertise_directory']

        for name in directories:
            if Directory.query.filter_by(master_uid=uid, name=name).first():
                # 已存在，则跳过
                continue

            directory = Directory(
                name=name,
                master_uid=uid,
                parent_id=0,
                top=0,
                type=1,
                is_default=True if name == 'fx_default_directory' else False
            )
            db.session.add(directory)

        db.session.commit()


class InitialSystem(object):
    """系统初始化，配置系统默认数据"""

    @staticmethod
    def init_admin():
        """初始化系统管理员"""
        for email in current_app.config['ADMINS']:
            if User.query.filter_by(email=email, is_admin=True).first():
                print('System user: %s already initial, exit!' % email)

                continue

            user = User()

            user.email = email
            user.username = email.split('@')[0]
            user.password = 'Mic#2009?!'
            user.time_zone = 'zh'
            user.confirmed = True
            user.is_admin = True

            db.session.add(user)

        db.session.commit()

        print('System user is initial!')

    @staticmethod
    def init_acl():
        """初始化权限管理"""

        # 检测是否已安装数据
        total_count = Ability.query.count()
        if total_count:
            print('Ability is initial, exit!')
            return False

        # 安装权限列表
        for acl in DEFAULT_ACLIST:
            ability = Ability(
                name=acl[0],
                title=acl[1]
            )
            db.session.add(ability)

        db.session.commit()

    @staticmethod
    def init_directory():
        """初始化默认目录"""

        default_name = DEFAULT_DIRECTORY['name']
        if Directory.query.filter_by(is_default=True).first():
            print('Default directory already initial, exit!')
            return False

        default_directory = Directory(
            name=default_name,
            is_default=True
        )
        db.session.add(default_directory)
        db.session.commit()

        print('Default directory is initial!')

    @staticmethod
    def init_asset():
        """初始化附件图片"""

        if Asset.query.filter_by(is_default=True).first():
            print('Default asset already initial, exit!')
            return False

        default_directory = Directory.query.filter_by(is_default=True).first()
        default_asset = Asset(directory=default_directory, **DEFAULT_ASSET)

        db.session.add(default_asset)
        db.session.commit()

        print('Default asset is initial!')

    @staticmethod
    def init_supplier():
        """初始化默认供应商"""

        if Supplier.query.filter_by(is_default=True).first():
            print('Default supplier already initial, exit!')
            return False

        default_supplier = Supplier(
            **DEFAULT_SUPPLIER
        )

        db.session.add(default_supplier)
        db.session.commit()

        print('Default supplier is initial!')

    @staticmethod
    def init_express():
        """初始化默认物流公司"""

        if Express.query.filter_by(is_default=True).first():
            print('Default express already initial, exit!')
            return False

        default_express = Express(**DEFAULT_EXPRESS)

        db.session.add(default_express)
        db.session.commit()

        print('Default express is initial!')

    @staticmethod
    def init_open_country():
        """初始化开通的国家"""
        if Country.query.filter_by(name='中国').first():
            print('Default country already initial, exit!')
            return False

        country = Country(
            name='中国',
            en_name='china',
            code='CN',
            status=True
        )
        db.session.add(country)

        db.session.commit()

        print('Default country is initial!')
