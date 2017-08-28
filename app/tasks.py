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
from app.models import Currency, Site


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
            default_currency = Currency.query.filter_by(master_uid=master_uid, code=default_currency_code).first()
            if default_currency is None:
                continue
            default_currency.value = default_value

            # 更新其他货币值
            all_currencies = Currency.query.filter_by(master_uid=master_uid).all()
            for currency in all_currencies:
                code = currency.code
                if response_currency.get(code):
                    new_currency_value = response_currency.get(code)

                    currency.value = new_currency_value.get('rate')
                    currency.last_updated = string_to_timestamp(new_currency_value.get('updatetime'))

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
