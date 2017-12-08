# -*- coding: utf-8 -*-
import smtplib
import urllib
import json
from email.mime.text import MIMEText
from flask import current_app
from flask_mail import Message
from app import db
from app.extensions import flask_celery
from app.utils import string_to_timestamp
from app.models import Currency, Site, Order, OrderItem,ProductSku
from datetime import datetime, timedelta
from app.summary import OrderDeal

@flask_celery.task(bind=True)
def add_together(self, a, b):
    return a + b


@flask_celery.task(bind=True)
def async_currency_rate(self):
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


@flask_celery.task(
    bind=True,
    igonre_result=True,
    default_retry_delay=300,
    max_retries=5)
def remind(self, primary_key):
    """
    Send the remind email to user when registered.
    Using Flask-Mail.
    """
    from app.models import Reminder

    reminder = Reminder.query.get(primary_key)

    msg = MIMEText(reminder.text)
    msg['Subject'] = 'Welcome!'
    msg['FROM'] = ''
    msg['TO'] = reminder.email

    try:
        smtp_server = smtplib.SMTP('localhost')
        smtp_server.starttls()
        smtp_server.login('user', 'password')
        smtp_server.sendmail('email', [reminder.email], msg.as_string())

        smtp_server.close()

        return
    except Exception as err:
        self.retry(exc=err)


def on_reminder_save(mapper, connect, self):
    """Callback for task remind."""
    remind.apply_async(args=(self.id), eta=self.date)


@flask_celery.task
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    from .wsgi_aux import app

    with app.app_context():
        app.mail.send(msg)


@flask_celery.task
def sales_statistics(order_id):
    """主账户、各店铺 销售订单付款统计"""
    OrderDeal(order_id).order_pay()

    # from app.models import MasterStatistics, StoreStatistics

    # # 订单对象
    # order_obj = Order.query.filter_by(id=order_id).first()
    # if order_obj == None:
    #     return
    # # 订单明细列表
    # items_obj_list = order_obj.items

    # # 订单支付金额
    # income = float(order_obj.pay_amount)
    # # 该订单利润金额
    # profit = 0.0
    # for item in items_obj_list:
    #     sku = ProductSku.query.filter_by(id=item.sku_id).first()
    #     profit += round((float(item.deal_price) - float(sku.cost_price))
    #                     * item.quantity - float(item.discount_amount), 2)

    # # 支付时间
    # created_at = datetime.fromtimestamp(order_obj.created_at)
    # # 该订单年、月
    # year = created_at.strftime("%Y")
    # month = created_at.strftime("%Y%m")
    # # 上一年
    # last_year = (str)(created_at.year - 1)
    # # 上一月
    # last_month = (created_at - timedelta(days=created_at.day)
    #               ).strftime("%Y%m")
    # # 上年同一月
    # last_year_month = last_year + str(created_at.month)

    # try:

    #     # 主账户按年统计处理
    #     master_statistics_last_year = MasterStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=last_year, type=2).first()
    #     master_statistics_year = MasterStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=year, type=2).first()
    #     if master_statistics_year == None:
    #         # 如果有同比数据
    #         if master_statistics_last_year != None:
    #             # 销售同比
    #             income_yoy = round(
    #                 income / float(master_statistics_last_year.income) * 100, 2)
    #             # 利润同比
    #             profit_yoy = round(
    #                 profit / float(master_statistics_last_year.profit) * 100, 2)
    #         else:
    #             income_yoy = None
    #             profit_yoy = None

    #         master_statistics = MasterStatistics(
    #             master_uid=order_obj.master_uid,
    #             time=year,
    #             type=2,
    #             income=income,
    #             profit=profit,
    #             income_yoy=income_yoy,
    #             profit_yoy=profit_yoy,
    #         )
    #         db.session.add(master_statistics)
    #     else:
    #         master_statistics_year.income = float(master_statistics_year.income) + income
    #         master_statistics_year.profit = float(master_statistics_year.profit) + profit
    #         if master_statistics_last_year != None:
    #             # 销售同比
    #             master_statistics_year.income_yoy = round(
    #                 master_statistics_year.income / float(master_statistics_last_year.income) * 100, 2)
    #             # 利润同比
    #             master_statistics_year.profit_yoy = round(
    #                 master_statistics_year.profit / float(master_statistics_last_year.profit) * 100, 2)

    #     # 主账户按月统计处理
    #     master_statistics_last_month = MasterStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=last_month, type=1).first()

    #     master_statistics_last_year_month = MasterStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=last_year_month, type=1).first()

    #     master_statistics_month = MasterStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=month, type=1).first()

    #     if master_statistics_month == None:
    #         # 如果有同比数据
    #         if master_statistics_last_year_month != None:
    #             # 销售同比
    #             income_yoy = round(
    #                 income / float(master_statistics_last_year_month.income) * 100, 2)
    #             # 利润同比
    #             profit_yoy = round(
    #                 profit / float(master_statistics_last_year_month.profit) * 100, 2)
    #         else:
    #             income_yoy = None
    #             profit_yoy = None

    #         # 如果有环比数据
    #         if master_statistics_last_month != None:
    #             # 销售环比
    #             income_mom = round(
    #                 income / float(master_statistics_last_month.income) * 100, 2)
    #             # 利润环比
    #             profit_mom = round(
    #                 profit / float(master_statistics_last_month.profit) * 100, 2)
    #         else:
    #             income_mom = None
    #             profit_mom = None

    #         master_statistics = MasterStatistics(
    #             master_uid=order_obj.master_uid,
    #             time=month,
    #             type=1,
    #             income=income,
    #             profit=profit,
    #             income_yoy=income_mom,
    #             profit_yoy=profit_mom,
    #         )
    #         db.session.add(master_statistics)
    #     else:
    #         master_statistics_month.income = float(master_statistics_month.income) + income
    #         master_statistics_month.profit = float(master_statistics_month.profit) + profit
    #         if master_statistics_last_year_month != None:
    #             # 销售同比
    #             master_statistics_month.income_yoy = round(
    #                 master_statistics_month.income / float(master_statistics_last_year_month.income) * 100, 2)
    #             # 利润同比
    #             master_statistics_month.profit_yoy = round(
    #                 master_statistics_month.profit / float(master_statistics_last_year_month.profit) * 100, 2)

    #         if master_statistics_last_month != None:
    #             # 销售环比
    #             master_statistics_month.income_mom = round(
    #                 master_statistics_month.income / float(master_statistics_last_month.income) * 100, 2)
    #             # 利润环比
    #             master_statistics_month.profit_mom = round(
    #                 master_statistics_month.profit / float(master_statistics_last_month.profit) * 100, 2)



    #     # 子账户按年统计处理
    #     store_statistics_last_year = StoreStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=last_year,store_id=order_obj.store_id, type=2).first()
    #     store_statistics_year = StoreStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid,store_id=order_obj.store_id, time=year, type=2).first()
    #     if store_statistics_year == None:
    #         # 如果有同比数据
    #         if store_statistics_last_year != None:
    #             # 销售同比
    #             income_yoy = round(
    #                 income / float(store_statistics_last_year.income) * 100, 2)
    #             # 利润同比
    #             profit_yoy = round(
    #                 profit / float(store_statistics_last_year.profit) * 100, 2)
    #         else:
    #             income_yoy = None
    #             profit_yoy = None

    #         store_statistics = StoreStatistics(
    #             master_uid=order_obj.master_uid,
    #             store_id=order_obj.store_id,
    #             time=year,
    #             type=2,
    #             income=income,
    #             profit=profit,
    #             income_yoy=income_yoy,
    #             profit_yoy=profit_yoy,
    #         )
    #         db.session.add(store_statistics)
    #     else:
    #         store_statistics_year.income = float(store_statistics_year.income) + income
    #         store_statistics_year.profit = float(store_statistics_year.profit) + profit
    #         if store_statistics_last_year != None:
    #             # 销售同比
    #             store_statistics_year.income_yoy = round(
    #                 store_statistics_year.income / float(store_statistics_last_year.income) * 100, 2)
    #             # 利润同比
    #             store_statistics_year.profit_yoy = round(
    #                 store_statistics_year.profit / float(store_statistics_last_year.profit) * 100, 2)

    #     # 子账户按月统计处理
    #     store_statistics_last_month = StoreStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=last_month,store_id=order_obj.store_id, type=1).first()

    #     store_statistics_last_year_month = StoreStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=last_year_month,store_id=order_obj.store_id, type=1).first()

    #     store_statistics_month = StoreStatistics.query.filter_by(
    #         master_uid=order_obj.master_uid, time=month,store_id=order_obj.store_id, type=1).first()

    #     if store_statistics_month == None:
    #         # 如果有同比数据
    #         if store_statistics_last_year_month != None:
    #             # 销售同比
    #             income_yoy = round(
    #                 income / float(store_statistics_last_year_month.income) * 100, 2)
    #             # 利润同比
    #             profit_yoy = round(
    #                 profit / float(store_statistics_last_year_month.profit) * 100, 2)
    #         else:
    #             income_yoy = None
    #             profit_yoy = None

    #         # 如果有环比数据
    #         if store_statistics_last_month != None:
    #             # 销售环比
    #             income_mom = round(
    #                 income / float(store_statistics_last_month.income) * 100, 2)
    #             # 利润环比
    #             profit_mom = round(
    #                 profit / float(store_statistics_last_month.profit) * 100, 2)
    #         else:
    #             income_mom = None
    #             profit_mom = None

    #         store_statistics = StoreStatistics(
    #             master_uid=order_obj.master_uid,
    #             store_id=order_obj.store_id,
    #             time=month,
    #             type=1,
    #             income=income,
    #             profit=profit,
    #             income_yoy=income_mom,
    #             profit_yoy=profit_mom,
    #         )
    #         db.session.add(store_statistics)
    #     else:
    #         store_statistics_month.income = float(store_statistics_month.income) + income
    #         store_statistics_month.profit = float(store_statistics_month.profit) + profit
    #         if store_statistics_last_year_month != None:
    #             # 销售同比
    #             store_statistics_month.income_yoy = round(
    #                 store_statistics_month.income / float(store_statistics_last_year_month.income) * 100, 2)
    #             # 利润同比
    #             store_statistics_month.profit_yoy = round(
    #                 store_statistics_month.profit / float(store_statistics_last_year_month.profit) * 100, 2)

    #         if store_statistics_last_month != None:
    #             # 销售环比
    #             store_statistics_month.income_mom = round(
    #                 store_statistics_month.income / float(store_statistics_last_month.income) * 100, 2)
    #             # 利润环比
    #             store_statistics_month.profit_mom = round(
    #                 store_statistics_month.profit / float(store_statistics_last_month.profit) * 100, 2)

    #     db.session.commit()
    # except Exception:
    #     db.session.rollback()
    #     raise