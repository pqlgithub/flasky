# -*- coding: utf-8 -*-
import smtplib
from flask import current_app
from email.mime.text import MIMEText
from email.utils import formataddr

__all__ = [
    'BaseMessage',
    'WxMessage',
    'SmsMessage',
    'EmailMessage'
]


class BaseMessage(object):
    """发送消息基类"""

    def send(self, subject, body, to, name):
        raise NotImplementedError('还没实现send方法')


class WxMessage(BaseMessage):
    """发送微信功能"""

    def __init__(self):
        pass

    def send(self, subject, body, to, name):
        current_app.logger.debug('微信发送成功')


class SmsMessage(BaseMessage):
    """发送短信功能"""

    def __init__(self):
        pass

    def send(self, subject, body, to, name):
        current_app.logger.debug('短信发送成功')


class EmailMessage(BaseMessage):
    """发送邮件"""

    def __init__(self, email, user, pwd):
        self.email = email
        self.user = user
        self.pwd = pwd

    def send(self, subject, body, to, name):
        """
        发送邮件
        :param subject: 邮件主题
        :param body: 邮件内容
        :param to: 收件人邮箱
        :param name: 收件人名称
        :return:
        """

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = formataddr([self.user, self.email])
        msg['To'] = formataddr([name, to])
        msg['Subject'] = subject

        server = smtplib.SMTP('smtp.126.com', 25)
        server.login(self.email, self.pwd)
        server.sendmail(self.email, [to, ], msg.as_string())
        server.quit()
