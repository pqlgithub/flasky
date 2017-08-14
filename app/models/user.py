# -*- coding: utf-8 -*-
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from ..utils import timestamp
from ..constant import SUPPORT_DOMAINS,SUPPORT_LANGUAGES, SUPPORT_COUNTRIES, SUPPORT_CURRENCIES
from app import db, login_manager
from .store import Currency

__all__ = [
    'User',
    'Role',
    'Ability',
    'Site',
    'AnonymousUser'
]

# 定义user与role关系的辅助表
user_role_table = db.Table('users_roles',
                           db.Column(
                               'user_id', db.Integer, db.ForeignKey('users.id')),
                           db.Column(
                               'role_id', db.Integer, db.ForeignKey('roles.id')
                           ))

# 定义role与ability关系的辅助表
role_ability_table = db.Table('roles_abilities',
                              db.Column(
                                  'role_id', db.Integer, db.ForeignKey('roles.id')),
                              db.Column(
                                  'ability_id', db.Integer, db.ForeignKey('abilities.id')
                              ))


class User(UserMixin, db.Model):
    """This User model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # 主账号，默认为0
    master_uid = db.Column(db.Integer, index=True, default=0)

    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    # 系统默认管理员
    is_admin = db.Column(db.Boolean, default=False)

    # 真实资料信息
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.Integer, default=timestamp)
    avatar = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    description = db.Column(db.String(140))

    # 是否配置站点信息
    is_setting = db.Column(db.Boolean, default=False)

    # 本地化
    locale = db.Column(db.String(4), default='zh')
    language = db.Column(db.String(4), default='en')
    time_zone = db.Column(db.String(20), nullable=False)
    # disabled at the time
    disabled_at = db.Column(db.Integer, default=0)
    # if online or offline
    online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.Integer, default=timestamp)

    created_at = db.Column(db.Integer, default=timestamp)
    # update time of last time
    update_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)


    # 用户角色
    roles = db.relationship(
        'Role', secondary=user_role_table, backref='users'
    )

    @property
    def role_group(self):
        return ' / '.join(self.has_roles())

    def has_roles(self):
        return [role.title for role in self.roles]

    def add_roles(self, *roles):
        """添加用户角色"""
        self.roles.extend([role for role in roles if role not in self.roles])

    def update_roles(self, *roles):
        """重置角色"""
        self.roles = [role for role in roles]

    def remove_roles(self, *roles):
        """删除用户角色"""
        self.roles = [role for role in self.roles if role not in roles]


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        """生成一个令牌，有效期默认为一小时."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})


    @property
    def is_master(self):
        """是否为主账号"""
        return self.master_uid == 0

    def mark_as_setting(self):
        """设置已配置站点信息"""
        self.is_setting = True
    

    def confirm(self, token):
        """检验令牌，如果检验通过，则把新添加的confirmed 属性设为True."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False

        # 更新状态
        self.confirmed = True
        db.session.add(self)
        db.session.commit()

        return True

    def ping(self):
        """每次收到用户的请求时都要调用ping()方法"""
        self.last_seen = timestamp()
        last_online = self.online
        self.online = True

        db.session.add(self)

        return last_online != self.online

    # API基于令牌的认证
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None

        return User.query.get(data['id'])

    def g_avatar(self, size):
        """user avatar"""
        return 'http://www.gravatar.com/avatar/' + md5(self.email.encode('utf8')).hexdigest() + '?d=mm&s=' + str(size)

    @staticmethod
    def make_unique_username(username):
        if User.query.filter_by(username=username).first() == None:
            return username
        version = 2
        while True:
            new_username = username + str(version)
            if User.query.filter_by(username=new_username).first() == None:
                break
            version += 1
        return new_username


    def __repr__(self):
        return '<User %r>' % self.username


class Role(db.Model):
    """
    Subclass this for your roles
    """
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)

    master_uid = db.Column(db.Integer, index=True, default=0)

    name = db.Column(db.String(50), index=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    abilities = db.relationship(
        'Ability', secondary=role_ability_table, backref='roles'
    )

    @property
    def ability_group(self):
        return ' / '.join(self.has_abilities())

    def has_abilities(self):
        return [ability.name for ability in self.abilities]

    def add_abilities(self, *abilities):
        """批量添加权限"""
        for ability in abilities:
            existing_ability = Ability.query.filter_by(name=ability).first()
            if not existing_ability:
                existing_ability = Ability(ability)
                db.session.add(existing_ability)
                db.session.commit()
            self.abilities.append(existing_ability)

    def update_abilities(self, *abilities):
        self.abilities = [ability for ability in abilities]

    def remove_abilities(self, *abilities):
        """批量删除权限"""
        for ability in abilities:
            existing_ability = Ability.query.filter_by(name=ability).first()
            if existing_ability and existing_ability in self.abilities:
                self.abilities.remove(existing_ability)


    def __init__(self, name, master_uid, title=None, description=None):
        self.name = name.lower()
        self.title = title
        self.description = description
        self.master_uid = master_uid


    def __repr__(self):
        return '<Role {}>'.format(self.name)

    def __str__(self):
        return self.name


class Ability(db.Model):
    __tablename__ = 'abilities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, index=True)
    title = db.Column(db.String(100), nullable=False)

    def __init__(self, name, title):
        self.name = name.lower()
        self.title = title


    def __repr__(self):
        return '<Ability {}>'.format(self.name)


class AnonymousUser(AnonymousUserMixin):
    locale = None
    def belong_roles(self):
        return []

    @property
    def is_setting(self):
        return False


login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    """使用指定的标识符加载用户"""
    return User.query.get(int(user_id))


class Site(db.Model):
    """站点配置信息"""

    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, unique=True, index=True)

    company_name = db.Column(db.String(50), unique=True, index=True, nullable=False)
    company_abbr = db.Column(db.String(10), nullable=True)

    locale = db.Column(db.String(4), default='zh')
    country = db.Column(db.String(30), nullable=True)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'))
    # 行业范围
    domain = db.Column(db.SmallInteger, default=1)
    description = db.Column(db.Text)

    created_at = db.Column(db.Integer, default=timestamp)
    update_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)


    @property
    def currency(self):
        return self.default_currency.code if self.default_currency else ''


    @property
    def default_currency(self):
        return Currency.query.get(self.currency_id)


    @property
    def locale_label(self):
        for l in SUPPORT_LANGUAGES:
            if l[1] == self.locale:
                return l


    @property
    def country_label(self):
        for c in SUPPORT_COUNTRIES:
            if c[1] == self.country:
                return c


    @property
    def domain_label(self):
        for d in SUPPORT_DOMAINS:
            if d[0] == self.domain:
                return d

    def __repr__(self):
        return '<Site %r>' % self.company_name
