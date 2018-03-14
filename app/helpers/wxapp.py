# -*- coding: utf-8 -*-
import os
import binascii
import base64
import json
import hashlib
import requests
import urllib.parse
from Crypto.Cipher import AES
from flask import current_app
from app.utils import Map


class WxAppError(Exception):
    def __init__(self, msg):
        super(WxAppError, self).__init__(msg)


class WxApp(object):
    """
    微信小程序第三方平台API
    """
    component_host_url = 'https://api.weixin.qq.com/cgi-bin/component'

    # 小程序API服务域名
    wxa_host_url = 'https://api.weixin.qq.com/wxa'

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

    def exchange_authorizer_token(self, auth_code_value):
        """
        该API用于使用授权码换取授权公众号或小程序的授权信息，并换取authorizer_access_token和authorizer_refresh_token
        """
        payload = {
            'component_appid': self.component_app_id,
            'authorization_code': auth_code_value
        }
        url = '%s/api_query_auth?component_access_token=%s' % (self.component_host_url,
                                                               self.component_access_token)
        result = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(result)

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
        result = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(result)

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
        result = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(result)

    def get_template_draft_list(self):
        """获取草稿箱内的所有临时代码草稿"""
        url = '%s/gettemplatedraftlist?access_token=%s' % (self.wxa_host_url, self.component_access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def get_template_list(self):
        """获取代码模版库中的所有小程序代码模版"""
        url = '%s/gettemplatelist?access_token=%s' % (self.wxa_host_url, self.component_access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def add_to_template(self, draft_id=0):
        """将草稿箱的草稿选为小程序代码模版"""
        payload = {
            'draft_id': draft_id
        }
        url = '%s/addtotemplate?access_token=%s' % (self.wxa_host_url, self.component_access_token)
        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def delete_template(self, template_id=0):
        """删除指定小程序代码模版"""
        payload = {
            'template_id': template_id
        }
        url = '%s/deletetemplate?access_token=%s' % (self.wxa_host_url, self.component_access_token)
        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def jscode2session(self, app_id, js_code):
        """
        通过code换取openid和session_key
        https://api.weixin.qq.com/sns/component/jscode2session?appid=APPID&js_code=JSCODE&grant_type=authorization_code&
        component_appid=COMPONENT_APPID&component_access_token=ACCESS_TOKEN
        """
        url = ('https://api.weixin.qq.com/sns/component/jscode2session?appid={}&js_code={}'
               '&grant_type=authorization_code&component_appid={}&component_access_token={}').format(
            app_id, js_code, self.component_app_id, self.component_access_token)
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

        # if decrypted['watermark']['appid'] != self.app_id:
        #    raise Exception('Invalid Buffer')

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


class WxaOpen3rd(object):
    """
    第三方平台更新授权小程序API
    """
    # 小程序API服务域名
    wxa_host_url = 'https://api.weixin.qq.com/wxa'

    def __init__(self, access_token=None):
        self.access_token = access_token

    def modify_domain(self, action='add', request_domain=[], wsrequest_domain=[], upload_domain=[], download_domain=[]):
        """
        设置小程序服务器域名
        action: add添加, delete删除, set覆盖, get获取。当参数是get时不需要填四个域名字段
        """
        payload = {
            'action': action
        }

        if action in ('add', 'delete', 'set'):
            payload['requestdomain'] = request_domain
            payload['wsrequestdomain'] = wsrequest_domain
            payload['uploaddomain'] = upload_domain
            payload['downloaddomain'] = download_domain

        url = '%s/modify_domain?access_token=%s' % (self.wxa_host_url, self.access_token)
        result = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(result)

    def set_webview_domain(self, action='add', view_domain=[]):
        """
        设置小程序业务域名
        action: add添加, delete删除, set覆盖, get获取。当参数是get时不需要填webviewdomain字段。
        如果没有action字段参数，则默认见开放平台第三方登记的小程序业务域名全部添加到授权的小程序中
        """
        payload = {
            'action': action
        }
        if action in ('add', 'delete', 'set'):
            payload['webviewdomain'] = view_domain

        url = '%s/setwebviewdomain?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def bind_tester(self, wechatid):
        """
        绑定微信用户为小程序体验者
        """
        payload = {
            'wechatid': wechatid
        }
        url = '%s/bind_tester?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def unbind_tester(self, wechatid):
        """
        解除绑定小程序的体验者
        """
        payload = {
            'wechatid': wechatid
        }
        url = '%s/unbind_tester?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def commit(self, template_id=0, ext_json={}, user_version='V1.0', user_desc=''):
        """为授权的小程序帐号上传小程序代码"""
        payload = {
            'template_id': template_id,  # 代码库中的代码模版ID
            'ext_json': json.dumps(ext_json),  # 第三方自定义的配置
            'user_version': user_version,  # 代码版本号，开发者可自定义
            'user_desc': user_desc  # 代码描述，开发者可自定义
        }
        url = '%s/commit?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def get_qrcode(self, path=None):
        """获取体验小程序的体验二维码"""
        url = '%s/get_qrcode?access_token=%s' % (self.wxa_host_url, self.access_token)
        if path:
            url += '&path=%s' % urllib.parse.urlencode(path)

        res = requests.get(url)

        return res

    def get_category(self):
        """获取授权小程序帐号的可选类目"""
        url = '%s/get_category?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def get_pages(self):
        """获取小程序的第三方提交代码的页面配置"""
        url = '%s/get_page?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def submit_audit(self, item_list=[]):
        """将第三方提交的代码包提交审核"""
        payload = {
            'item_list': item_list
        }
        url = '%s/submit_audit?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=bytes(json.dumps(payload, ensure_ascii=False), encoding='utf-8'))

        return self._intercept_result(res)

    def get_audit_status(self, auditid):
        """
        查询某个指定版本的审核状态
        status:	审核状态，其中0为审核成功，1为审核失败，2为审核中
        """
        payload = {
            'auditid': auditid
        }
        url = '%s/get_auditstatus?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def get_latest_audit_status(self):
        """查询最新一次提交的审核状态"""
        url = '%s/get_latest_auditstatus?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.get(url)

        return self._intercept_result(res)

    def release(self):
        """发布已通过审核的小程序"""
        payload = {}
        url = '%s/release?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def change_visit_status(self, action='open'):
        """
        修改小程序线上代码的可见状态
        action:	设置可访问状态，发布后默认可访问，close为不可见，open为可见
        """
        payload = {
            'action': action
        }
        url = '%s/change_visitstatus?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def revert_code_release(self):
        """小程序版本回退"""
        url = '%s/revertcoderelease?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def undo_code_audit(self):
        """
        小程序审核撤回
        单个帐号每天审核撤回次数最多不超过1次，一个月不超过10次。
        """
        url = '%s/undocodeaudit?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def gray_release(self, percent=10):
        """分阶段发布接口"""
        payload = {
            'gray_percentage': percent  # 灰度的百分比，1到100的整数
        }
        url = '%s/grayrelease?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def revert_gray_release(self):
        """取消分阶段发布"""
        url = '%s/revertgrayrelease?access_token=%s' % (self.wxa_host_url, self.access_token)

        res = requests.get(url)

        return self._intercept_result(res)

    def get_gray_release_plan(self):
        """
        查询当前分阶段发布详情
        status: 0:初始状态 1:执行中 2:暂停中 3:执行完毕 4:被删除
        """
        url = '%s/getgrayreleaseplan?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def change_wxa_search_status(self, status=0):
        """设置小程序隐私设置（是否可被搜索）"""
        payload = {
            'status': status
        }
        url = '%s/changewxasearchstatus?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.post(url, data=json.dumps(payload))

        return self._intercept_result(res)

    def get_wxa_search_status(self):
        """查询小程序当前隐私设置（是否可被搜索）"""
        url = '%s/getwxasearchstatus?access_token=%s' % (self.wxa_host_url, self.access_token)
        res = requests.get(url)

        return self._intercept_result(res)

    def _intercept_result(self, result):
        """返回请求结果"""
        result = Map(result.json())
        if result.get('errcode') and result.get('errcode') != 0:
            current_app.logger.warn('WxaOpen3rd res code: %d' % result.get('errcode'))
            errmsg = result.get('errmsg').split(':')
            raise WxAppError(errmsg[0])
        
        return result


class WxService(object):
    """微信小程序客服消息"""

    def __init__(self, token, encoding_aes_key):
        self.token = token
        self.key = base64.b64decode(encoding_aes_key + "=")

    def check_signature(self, timestamp, nonce, signature):
        """用SHA1算法生成安全签名
        @:param token: 验证
        @:param timestamp: 时间戳
        @:param nonce: 随机字符串
        @:param signature: 验证签名
        @:return: 是否匹配
        """
        sort_list = [self.token, timestamp, nonce]
        sort_list.sort()
        sha = hashlib.sha1()
        sha.update(''.join(sort_list).encode('utf-8'))
        tmp_sign = sha.hexdigest()

        return True if tmp_sign == signature else False


class WxReply(object):
    """微信小程序回复客服消息"""

    wxa_send_url = 'https://api.weixin.qq.com/cgi-bin/message'

    def __init__(self, access_token):
        self.access_token = access_token

    def send_message(self, data):
        url = '%s/custom/send?access_token=%s' % (self.wxa_send_url, self.access_token)
        result = requests.post(url, data=bytes(json.dumps(data, ensure_ascii=False), encoding='utf-8'))

        result = Map(result.json())
        if result.get('errcode') and result.get('errcode') != 0:
            current_app.logger.warn('WxReply res code: %d' % result.get('errcode'))
            raise WxAppError(result.get('errmsg'))

        return result


def gen_3rd_session_key():
    """生成长度为32位的hex字符串，用于第三方session的key"""
    return binascii.hexlify(os.urandom(16)).decode()

