# -*- coding: utf-8 -*-
from flask import g, request, current_app

from .. import db
from . import api
from app.models import WxToken, User, UserIdType
from .utils import full_response, R200_OK, custom_response
from app.helpers import WxApp, WxAppError, MixGenId


@api.route('/accounts/wxa_login', methods=['POST'])
def verify_wxa_login():
    """
    小程序的新用户登录/注册
    1、如用户存在，则返回Token
    2、如用户不存在，则先自动注册，再返回Token
    3、解密用户信息：{
        "openId": "OPENID",
        "nickName": "NICKNAME",
        "gender": GENDER,
        "city": "CITY",
        "province": "PROVINCE",
        "country": "COUNTRY",
        "avatarUrl": "AVATARURL",
        "unionId": "UNIONID",
        "watermark":
        {
            "appid":"APPID",
            "timestamp":TIMESTAMP
        }
    }
    """
    js_code = request.json.get('code')
    encrypted_data = request.json.get('encrypted_data')
    iv = request.json.get('iv')
    auth_app_id = request.json.get('auth_app_id')

    if js_code and encrypted_data and iv:
        component_app_id = current_app.config['WX_APP_ID']
        wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()

        try:
            # 发起请求
            wxapi = WxApp(component_app_id=component_app_id,
                          component_app_secret=current_app.config['WX_APP_SECRET'],
                          component_access_token=wx_token.access_token)
            # 1、使用 code 换取 session key
            session_info = wxapi.jscode2session(auth_app_id, js_code)
        except WxAppError as err:
            current_app.logger.warn('登录失败：%s' % err)
            return custom_response('登录失败', 500, False)

        session_key = session_info.get('session_key')
        openid = session_info.get('openid')

        # 2、检测用户是否存在
        user = User.find_by_openid(openid)
        if not user:
            # 3、解密得到用户信息, 自动注册
            user_info = wxapi.decrypt(session_key, encrypted_data, iv)

            current_app.logger.warn(user_info)

            # 注册用户
            user = User()
            user.openid = openid
            user.email = openid
            # 随机生成密码
            user.password = MixGenId.gen_letters(10)
            user.id_type = UserIdType.BUYER
            user.confirmed = True
            user.time_zone = 'zh'
            user.username = User.make_unique_username(user_info['nickName'])
            user.avatar = user_info['avatarUrl']
            user.gender = user_info['gender']
            user.country = user_info['country']
            user.province = user_info['province']
            user.city = user_info['city']
            user.referer = 1

            db.session.add(user)
            db.session.commit()

        # 4、返回token
        expired_time = 7200
        user_token = {
            'uid': user.sn,
            'username': user.username,
            'avatar': user.avatar,
            'token': user.generate_auth_token(expiration=expired_time),
            'expiration': expired_time
        }
    else:
        current_app.logger.warn('Params: code[%s],encrypted_data[%s],iv[%s]' % (js_code, encrypted_data, iv))
        return custom_response('登录失败', 500, False)

    return full_response(R200_OK, user_token)



