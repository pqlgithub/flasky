# -*- coding: utf-8 -*-
import os
import binascii
import base64
import json
import requests
from Crypto.Cipher import AES


class WxApp(object):
    """
    微信小程序API
    """

    def __init__(self, app_id=None, app_secret=None):
        self.app_id = app_id
        self.app_secret = app_secret

    def jscode2session(self, js_code):
        """
        通过code换取openid和session_key
        https://api.weixin.qq.com/sns/component/jscode2session?appid=APPID&js_code=JSCODE&grant_type=authorization_code&
        component_appid=COMPONENT_APPID&component_access_token=ACCESS_TOKEN
        """
        url = ('https://api.weixin.qq.com/sns/component/jscode2session?'
               'appid={}&secret={}&js_code={}&grant_type=authorization_code&'
               'component_appid={}&component_access_token={}').format(self.app_id, self.app_secret, js_code)
        result = requests.get(url)

        return result.json()

    def decrypt(self, session_key, encrypted_data, iv):
        """加密数据解密"""
        session_key = base64.b64decode(session_key)
        encrypted_data = base64.b64decode(encrypted_data)
        iv = base64.b64decode(iv)

        cipher = AES.new(session_key, AES.MODE_CBC, iv)

        decrypt_data = self._unpad(cipher.decrypt(encrypted_data))
        decrypted = json.loads(decrypt_data.decode())

        if decrypted['watermark']['appid'] != self.app_id:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]


def gen_3rd_session_key():
    """生成长度为32位的hex字符串，用于第三方session的key"""
    return binascii.hexlify(os.urandom(16)).decode()

