# -*- coding: utf-8 -*-

import sys
from flask_script import Command
from app import db
from app.constant import DEFAULT_ACLIST
from app.models import Ability


class InitialData(Command):
    """Install initial data of system"""

    def run(self):
        print('Initial system data!')

        # 安装权限列表
        self.init_acl()

        sys.exit(0)


    def init_acl(self):

        # 检测是否已安装数据
        total_count = Ability.query.count()
        if total_count:
            print('Ability is initial, exit!')
            sys.exit(0)

        # 安装权限列表
        for acl in DEFAULT_ACLIST:
            ability = Ability(
                name=acl[0],
                title=acl[1]
            )
            db.session.add(ability)

        db.session.commit()
