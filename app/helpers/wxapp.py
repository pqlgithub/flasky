# -*- coding: utf-8 -*-
import os
import binascii
import base64
import json
import requests
from Crypto.Cipher import AES
from flask import current_app
from app.utils import Map


class WxAppError(Exception):
    def __init__(self, msg):
        super(WxAppError, self).__init__(msg)


class WxApp(object):
    """
    微信小程序API
    """
    component_host_url = 'https://api.weixin.qq.com/cgi-bin/component'
    headers = {
        'content-type': 'application/json'
    }

    def __init__(self, component_app_id=None, component_app_secret=None, component_access_token=None):
        self.component_app_id = component_app_id
        self.component_app_secret = component_app_secret
        self.component_access_token = component_access_token

    def get_component_token(self, verify_ticket):
        """
        获取第三方平台component_access_token, 每个令牌是存在有效期（2小时）的，且令牌的调用不是无限制的，
        请第三方平台做好令牌的管理，在令牌快过期时（比如1小时50分）再进行刷新
        返回结果示例:
        {"component_access_token":"61W3mEpU66027wgNZ_MhGHNQDHnFATkDa9-2llqrMBjUwxRSNPbVsMmyD-
        yq8wZETSoE5NQgecigDrSHkPtIYA", "expires_in":7200}
        """
        payload = {
            'component_appid': self.component_app_id,
            'component_appsecret': self.component_app_secret,
            'component_verify_ticket': verify_ticket
        }
        current_app.logger.debug('Request params: %s' % payload)

        url = '%s/api_component_token' % self.component_host_url
        result = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(result)
    
    def get_pre_auth_code(self):
        """
        该API用于获取预授权码。预授权码用于公众号或小程序授权时的第三方平台方安全验证
        返回结果示例:
        {"pre_auth_code":"Cx_Dk6qiBE0Dmx4EmlT3oRfArPvwSQ-oa3NL_fwHM7VI08r52wazoZX2Rhpz1dEw","expires_in":600}
        """
        payload = {
            'component_appid': self.component_app_id
        }
        url = '%s/api_create_preauthcode?component_access_token=%s' % (self.component_host_url,
                                                                       self.component_access_token)
        result = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(result)

    def exchange_authorizer_info(self, auth_code_value):
        """
        该API用于使用授权码换取授权公众号或小程序的授权信息，并换取authorizer_access_token和authorizer_refresh_token
        """
        payload = {
            'component_appid': self.component_app_id,
            'authorization_code': auth_code_value
        }
        url = '%s/api_query_auth?component_access_token=%s' % (self.component_host_url,
                                                               self.component_access_token)
        result = requests.post(url, data=payload)

        return result.json()

    def get_authorizer_token(self, authorizer_appid, authorizer_refresh_token):
        """
        获取（刷新）授权公众号或小程序的接口调用凭据（令牌）
        """
        payload = {
            'component_appid': self.component_app_id,
            'authorizer_appid': authorizer_appid,
            'authorizer_refresh_token': authorizer_refresh_token
        }
        url = '%s/api_authorizer_token?component_access_token=%s' % (self.component_host_url,
                                                                     self.component_access_token)
        result = requests.post(url, data=payload)

        return result.json()

    def get_authorizer_info(self, authorizer_appid):
        """
        获取小程序信息
        """
        payload = {
            'component_appid': self.component_app_id,
            'authorizer_appid': authorizer_appid
        }
        url = '%s/api_get_authorizer_info?component_access_token=%s' % (self.component_host_url,
                                                                        self.component_access_token)
        result = requests.post(url, data=payload)

        return result.json()

    def jscode2session(self, app_id, app_secret, js_code):
        """
        通过code换取openid和session_key
        https://api.weixin.qq.com/sns/component/jscode2session?appid=APPID&js_code=JSCODE&grant_type=authorization_code&
        component_appid=COMPONENT_APPID&component_access_token=ACCESS_TOKEN
        """
        url = ('https://api.weixin.qq.com/sns/component/jscode2session?'
               'appid={}&secret={}&js_code={}&grant_type=authorization_code&'
               'component_appid={}&component_access_token={}').format(app_id, app_secret, js_code,
                                                                      self.component_app_id, self.component_app_secret)
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

    def _intercept_result(self, result):
        """返回请求结果"""
        result = Map(result.json())
        if result.get('errcode') and result.get('errcode') != 0:
            current_app.logger.warn('Response code: %d' % result.get('errcode'))
            raise WxAppError(result.get('errmsg'))

        return result


def gen_3rd_session_key():
    """生成长度为32位的hex字符串，用于第三方session的key"""
    return binascii.hexlify(os.urandom(16)).decode()

