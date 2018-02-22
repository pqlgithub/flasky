# -*- coding: utf-8 -*-
import json
import urllib
from flask import current_app
from app.extensions import fsk_celery

from app import db
from app.models import Currency, Site
from app.utils import string_to_timestamp
from app.helpers.initial import InitialSite


@fsk_celery.task(name='init.build_default_setting')
def build_default_setting(master_uid):
    """主账号创建成功后，自动为账号创建默认配置信息"""

    # 1、默认权限组
    InitialSite.install_role(master_uid)

    # 2、默认币种
    InitialSite.install_currency(master_uid)

    # 3、创建附件默认目录及分组目录
    InitialSite.install_directory(master_uid)

    # 4、创建默认


@fsk_celery.task(name='init.async_currency_rate')
def async_currency_rate():
    """定期同步当日汇率"""
    with current_app.app_context():
        host = current_app.config['CURRENCY_API_HOST']
        path = current_app.config['CURRENCY_API_SINGLE']
        appcode = current_app.config['CURRENCY_API_CODE']
        method = 'GET'
        bodys = {}

        all_sites = Site.query.all()
        for site in all_sites:
            master_uid = site.master_uid
            if site.currency_id is None or site.currency_id == '':
                continue

            querys = 'currency=' + site.currency
            url = host + path + '?' + querys

            current_app.logger.debug('Request url: %s' % url)

            req = urllib.request.Request(url)
            req.add_header('Authorization', 'APPCODE ' + appcode)
            response = urllib.request.urlopen(req)
            content = response.read()

            current_app.logger.debug('Request result: %s' % content)

            if type(content) != bytes:
                continue

            content_dict = json.loads(content.decode('utf8'))
            result = content_dict['result']
            response_currency = result['list']

            default_currency_code = result['currency']
            default_value = 1.0000

            # 更新默认值
            default_currency = Currency.query.filter_by(
                master_uid=master_uid, code=default_currency_code).first()
            if default_currency is None:
                continue
            default_currency.value = default_value

            # 更新其他货币值
            all_currencies = Currency.query.filter_by(
                master_uid=master_uid).all()
            for currency in all_currencies:
                code = currency.code
                if response_currency.get(code):
                    new_currency_value = response_currency.get(code)

                    currency.value = new_currency_value.get('rate')
                    currency.last_updated = string_to_timestamp(
                        new_currency_value.get('updatetime'))

        db.session.commit()

    return
