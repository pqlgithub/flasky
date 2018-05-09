# -*- coding: utf-8 -*-
import urllib.parse

from flask import flash, session
from flask_babelex import gettext
from app.utils import make_phoneverifycode
from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.ypclient import YunpianClient

from manage import app

config = app.config


def single_send(areacode, code, mobile,page):
    """单条发送接口"""

    apikey = config['YUNPIAN_APIKEY']
    if page == 'reset':
        mould = config['YUNPIAN_RESET_MOULD']
    else:
        mould = config['YUNPIAN_SIGNUP_MOULD']

    # 中国大陆
    if areacode == '+86':
        # 初始化client, apikey作为所有请求的默认值
        client = YunpianClient(apikey=apikey)

        # 模板、签名、模板id、apikey
        tpl_value = urllib.parse.urlencode({'#code#': code})  # 注意此处不要用sdk中的解码方法，超级傻逼
        # code 和 app是你模版里面的变量，我们使用py3的urllib.parse.urlencode方法对此参数进行转码，注意在｛｝中，需要在模版变量前后加上#，不然会返回参数不正确
        param = {YC.MOBILE: mobile, YC.TPL_ID: mould, YC.TPL_VALUE: tpl_value}
        r = client.sms().tpl_single_send(param)
        return r.msg()

    # 国际：
    else:
        pass


def send_phoneverifycode(phonenum, areacode, page, username):
    """发送短信"""
    # 判断是新注册用户还是重置密码
    if page == 'reset':
        if not username:
            if session.get('start_time'):
                del session['start_time']
            flash(gettext('没有该用户请重新输入。'), 'danger')
            return {'status': 0}
    else:
        if username:
            if session.get('start_time'):
                del session['start_time']
            flash(gettext('该手机号已注册。'), 'danger')
            return {'status': 0}

    # 生成手机验证码
    phoneverifycode = make_phoneverifycode()

    # 将手机验证码存放在session里
    session["phoneverifycode"] = phoneverifycode
    print('phoneverifycode', phoneverifycode)

    # 讲手机号存放到session里
    session["phonenum"] = phonenum
    print('phonenum', phonenum)

    # 将验证码通过短信发送
    msg_ret = single_send(areacode, phoneverifycode, phonenum, page)
    print(msg_ret)

    return {'status':1,'msg':msg_ret}
    # return {'status':1}





