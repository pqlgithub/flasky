# -*- coding: utf-8 -*-
"""
    微商城信息
    ~~~~~~~~~~~~~~~~~~
    
    @author mix
"""
from sqlalchemy import text, event
from sqlalchemy.sql import func
from flask import current_app
from app import db, config
from app.utils import timestamp
from app.models import Language, Currency
from app.helpers import MixGenId

__all__ = [
    'Shop',
    'ShopSeo'
]

# shop and language => N to N
shop_language_table = db.Table(
    'shop_language',
    db.Column('shop_id', db.Integer, db.ForeignKey('shops.id')),
    db.Column('language_id', db.Integer, db.ForeignKey('languages.id'))
)


class Shop(db.Model):
    """微商城信息"""
    
    __tablename__ = 'shops'
    
    id = db.Column(db.Integer, primary_key=True)
    
    master_uid = db.Column(db.Integer, index=True, default=0)
    # 生成编号
    sn = db.Column(db.String(32), unique=True, index=True, nullable=False)
    
    name = db.Column(db.String(64), index=True, nullable=False)
    # 默认域名(系统默认生成)
    visit_url = db.Column(db.String(100), unique=True, nullable=False)
    # 绑定的独立域名
    site_domain = db.Column(db.String(100), unique=True, nullable=True)
    favicon = db.Column(db.String(100), nullable=True)
    
    # 套餐标准，1、免费版 2、vip版本 3、定制版
    pricing = db.Column(db.SmallInteger, default=1)

    # 行业范围
    domain = db.Column(db.SmallInteger, default=1)
    copyright = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text)

    # 默认值，语言、国家、币种
    default_country = db.Column(db.Integer, default=0)
    default_language = db.Column(db.Integer, default=0)
    default_currency = db.Column(db.Integer, default=0)
    
    # 合作伙伴代码
    unicode = db.Column(db.String(64), nullable=True)
    
    # 状态: 开启、禁用
    status = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.Integer, default=timestamp)
    update_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def view_url(self):
        """官网地址"""

        # 正式环境
        if current_app.config['MODE'] == 'prod':
            return '%s://%s.%s' % (current_app.config['PROTOCOL'], self.serial_no, current_app.config['DOMAIN'])
        else:
            return '%s://127.0.0.1:5000/shop?alias=%s' % (current_app.config['PROTOCOL'], self.serial_no)

    
    @property
    def currency(self):
        """当前默认货币"""
        return Currency.query.get(int(self.default_currency))
    
    @property
    def language(self):
        """当前默认语言"""
        return Language.query.get(self.default_language)

    def update_languages(self, languages):
        """更新语言选项"""

        # 检测默认语言是否选中，如未选择，则自动添加
        default_language = Language.query.get(int(self.default_language))
        if default_language not in languages:
            languages.append(default_language)

        self.languages = [lang for lang in languages]
    
    
    @property
    def support_languages(self):
        """官网支持的语言, 默认语言设置为第一个"""
        support_languages =[]
        default_language = None
        for lang in self.languages:
            if lang.id == self.default_language:
                default_language = lang
            else:
                support_languages.append(lang)

        # 默认语言添加至第一个
        support_languages.insert(0, default_language)

        return support_languages

    def update_currencies(self, currencies):
        """更新支持的货币"""

        # 检测默认货币是否选中，如未选择，则自动添加
        default_currency = Currency.query.get(int(self.default_currency))
        if default_currency not in currencies:
            currencies.append(default_currency)

        self.currencies = [currency for currency in currencies]


    def update_countries(self, countries):
        """更新支持的国家"""
        self.countries = [country for country in countries]
        
    
    @staticmethod
    def make_unique_serial_no():
        serial_no = MixGenId.gen_shop_sn()
        if Shop.query.filter_by(sn=serial_no).first() == None:
            return serial_no
        while True:
            new_serial_no = MixGenId.gen_shop_sn()
            if Shop.query.filter_by(sn=new_serial_no).first() == None:
                break
        return new_serial_no
    
    
    @staticmethod
    def on_sync_change(mapper, connection, target):
        """同步事件"""
        target.visit_url = target.sn
        
        
    def to_json(self):
        """资源和JSON的序列化转换"""
        json_shop = {
            'rid': self.sn,
            'name': self.name,
            'favicon': self.favicon,
            'description': self.description,
            'copyright': self.copyright,
            'domain': self.domain,
            'status': self.status
        }
        return json_shop
    
    
    def __repr__(self):
        return '<Shop {}>'.format(self.name)


class ShopSeo(db.Model):
    """店铺SEO优化设置"""
    
    __tablename__ = 'shop_seo'
    
    id = db.Column(db.Integer, primary_key=True)
    
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'))
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'))
    
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    keywords = db.Column(db.String(255), nullable=True)


    def __repr__(self):
        return '<ShopSeo {}>'.format(self.site_id)


# 添加监听事件, 实现触发器
event.listen(Shop, 'before_insert', Shop.on_sync_change)