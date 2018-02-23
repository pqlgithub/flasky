# -*- coding: utf-8 -*-
import json
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from . import main
from .. import db, cache
from app.models import WxToken, WxAuthCode, WxMiniApp, WxAuthorizer, Store
from app.helpers import WxApp, WxAppError
from ..utils import Master, timestamp
from ..decorators import user_has, user_is


@main.route('/wxapps')
def wxapps():
    """小程序列表"""
    mini_apps = WxMiniApp.query.filter_by(master_uid=Master.master_uid()).all()

    return render_template('wxapp/index.html',
                           mini_apps=mini_apps)


@main.route('/wxapps/setting', methods=['GET', 'POST'])
def wxapp_setting():
    """配置小程序参数"""
    auth_app_id = request.values.get('auth_app_id')
    is_auth = False
    if not auth_app_id:
        return redirect(url_for('.wxapps'))

    # 根据auth_app_id获取auth access token
    wx_mini_app = WxMiniApp.query.filter_by(auth_app_id=auth_app_id).first()
    if wx_mini_app is None:
        # 获取小程序信息
        try:
            result = _get_authorizer_info(auth_app_id)
        except WxAppError as err:
            flash('小程序获取信息失败：%s，请重试！' % err, 'danger')
            return render_template('wxapp/index.html', auth_status=is_auth)

        current_app.logger.debug('Authorizer result %s' % result)

        authorizer_info = result.authorizer_info
        authorization_info = result.authorization_info
        # 新增
        new_serial_no = WxMiniApp.make_unique_serial_no()
        wx_mini_app = WxMiniApp(
            master_uid=Master.master_uid(),
            serial_no=new_serial_no,
            auth_app_id=auth_app_id,
            nick_name=authorizer_info.nick_name,
            head_img=authorizer_info.head_img,
            signature=authorizer_info.signature,
            user_name=authorizer_info.user_name,
            principal_name=authorizer_info.principal_name,
            service_type_info=json.dumps(authorizer_info.service_type_info),
            verify_type_info=json.dumps(authorizer_info.verify_type_info),
            business_info=json.dumps(authorizer_info.business_info),
            qrcode_url=authorizer_info.qrcode_url,
            mini_program_info=json.dumps(authorizer_info.mini_program_info),
            func_info=json.dumps(authorization_info.func_info)
        )
        db.session.add(wx_mini_app)

        # 同步增加一个关联店铺
        new_store = Store(
            master_uid=Master.master_uid(),
            operator_id=Master.master_uid(),
            name=authorizer_info.nick_name,
            serial_no=new_serial_no,
            description=authorizer_info.signature,
            platform=1,
            type=3,
            status=1
        )
        db.session.add(new_store)

        db.session.commit()

    is_auth = True
    return render_template('wxapp/setting.html',
                           auth_status=is_auth,
                           wx_mini_app=wx_mini_app.to_json())


@main.route('/wxapps/authorize')
def wxapp_authorize():
    """跳转授权页"""
    app_id = current_app.config['WX_APP_ID']
    back_url = '{}/open/wx/authorize_callback'.format(current_app.config['DOMAIN_URL'])
    auth_type = 2

    # 从缓存获取auth_code
    auth_code = cache.get('user_%d_wx_authorizer_auth_code' % Master.master_uid())
    if auth_code:
        return redirect('%s?auth_code=%s&is_cached=%d' % (back_url, auth_code, 1))

    # 获取预授权码
    pre_auth_code = _get_pre_auth_code()

    authorize_url = ('https://mp.weixin.qq.com/cgi-bin/componentloginpage?component_appid={}&pre_auth_code={}&'
                     'redirect_uri={}&auth_type={}').format(app_id, pre_auth_code, back_url, auth_type)

    return redirect(authorize_url)


def _get_authorizer_info(auth_app_id):
    """获取授权小程序账号信息"""
    component_app_id = current_app.config['WX_APP_ID']
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
    # 发起请求
    wx_app_api = WxApp(component_app_id=component_app_id,
                       component_app_secret=current_app.config['WX_APP_SECRET'],
                       component_access_token=wx_token.access_token)
    result = wx_app_api.get_authorizer_info(auth_app_id)

    return result


@cache.cached(timeout=600, key_prefix='wx_pre_auth_code')
def _get_pre_auth_code():
    """获取预授权码"""
    current_app.logger.warn('get by caching...')

    component_app_id = current_app.config['WX_APP_ID']
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()

    try:
        # 发起请求
        wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                           component_app_secret=current_app.config['WX_APP_SECRET'],
                           component_access_token=wx_token.access_token)

        result = wx_app_api.get_pre_auth_code()
    except WxAppError as err:
        current_app.logger.warn('Request pre_auth_code error: {}'.format(err))
        return None

    return result.pre_auth_code
