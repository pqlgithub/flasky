# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Message
from app.extensions import fsk_celery

from app import db
from app.models import Currency, Site
from app.summary import StoreSales, StoreProductSales, SalesLog
from app.utils import string_to_timestamp
from app.helpers.initial import InitialSite


@fsk_celery.task(
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


@fsk_celery.task
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    from ..wsgi_aux import app

    with app.app_context():
        app.mail.send(msg)
