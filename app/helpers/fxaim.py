# -*- coding: utf-8 -*-
import os
import binascii
import base64
import json
import hashlib
import requests
from flask import current_app, redirect
from app.utils import Map


class Fxaim(object):
    """
    智能图像生成接口
    """
    # API服务域名
    aim_host_url = 'http://127.0.0.1:8080/api/v1.0'

    headers = {
        'Content-Type': 'application/json'
    }

    def get_wxa_poster(self, data):
        """
        获取小程序码推广海报
        :param data: 参数字典
        :return: image_url
        """

        current_app.logger.warn('Wxa poster data: %s' % data)

        url = '%s/maker/wxa_poster' % self.aim_host_url
        result = requests.post(url, data=json.dumps(data), headers=self.headers)

        return self._intercept_result(result)

    def _intercept_result(self, result):
        """返回请求结果"""
        result = Map(result.json())

        current_app.logger.warn('Wxa poster result: %s' % result)

        if result.success:
            return result.data
