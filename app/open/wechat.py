# -*- coding: utf-8 -*-
import json
from flask import current_app, request, redirect, url_for, render_template
import xml.etree.cElementTree as ET

from . import open
from .. import db, cache
from app.models import WxToken, WxAuthorizer
from app.helpers import WXBizMsgCrypt, WxAppError, WxApp, WxPay, WxPayError, WxService
from app.utils import Master, custom_response, timestamp


@open.route('/wx/authorize_notify', methods=['GET', 'POST'])
def authorize_notify():
    """接收取消授权通知、授权成功通知、授权更新通知"""
    signature = request.values.get('signature')
    encrypt_type = request.values.get('encrypt_type')
    timestamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')
    msg_signature = request.values.get('msg_signature')
    post_data = request.get_data()

    # 解密接口
    des_key = current_app.config['WX_APP_DES_KEY']
    token = current_app.config['WX_APP_TOKEN']
    app_id = current_app.config['WX_APP_ID']

    decrypt = WXBizMsgCrypt(token, des_key, app_id)
    ret, decrypt_content = decrypt.DecryptMsg(post_data, msg_signature, timestamp, nonce)
    # 解密成功
    if ret == 0:
        # 更新ticket
        current_app.logger.warn("decrypt content: %s" % decrypt_content)

        xml_tree = ET.fromstring(decrypt_content)
        info_type = xml_tree.find('InfoType').text
        app_id = xml_tree.find('AppId').text
        create_time = xml_tree.find('CreateTime').text

        current_app.logger.debug('Parse app_id:[%s], create_time[%s]' % (app_id, create_time))

        if info_type == 'component_verify_ticket':  # 推送component_verify_ticket
            verify_ticket = xml_tree.find('ComponentVerifyTicket').text

            current_app.logger.debug('Component verify ticket: %s' % verify_ticket)

            # 设置缓存DB,每隔10分钟定时推送component_verify_ticket,
            # timeout是缓存过期时间，默认为0，永不过期
            cache.set('wx_component_verify_ticket', verify_ticket, timeout=0)

        elif info_type == 'authorized':  # 授权成功通知
            authorizer_app_id = xml_tree.find('AuthorizerAppid').text
            authorizer_code = xml_tree.find('AuthorizationCode').text
            authorizer_expired_time = xml_tree.find('AuthorizationCodeExpiredTime').text

            current_app.logger.warn('Authorizer [%s][%s][%s]' % (authorizer_app_id, authorizer_code,
                                                                 authorizer_expired_time))

        elif info_type == 'unauthorized':  # 取消授权通知
            pass

        elif info_type == 'updateauthorized':  # 授权更新通知
            pass

    else:
        current_app.logger.warn('Error code: %d' % ret)

    return 'success'


@open.route('/wx/authorize_callback', methods=['GET'])
def authorize_callback():
    """授权成功后回调url"""
    current_app.logger.warn('request content {}'.format(request.values))

    auth_code = request.values.get('auth_code')
    expires_in = request.values.get('expires_in')
    is_cached = request.values.get('is_cached')

    if auth_code is None:
        return custom_response(False, '授权失败，Auth Code 为空！')

    if not is_cached:
        # 设置缓存
        cache.set('user_%d_wx_authorizer_auth_code' % Master.master_uid(), auth_code, timeout=expires_in)

    try:
        auth_app_id = _exchange_authorizer_token(auth_code)
        if not auth_app_id:
            return render_template('wxapp/authorize_result.html', errmsg='小程序获取授权信息失败，请重新授权！')
    except WxAppError as err:
        return render_template('wxapp/authorize_result.html', errmsg='小程序获取授权信息失败：%s，请刷新！' % err)

    # 授权完成，跳转至设置页
    return redirect('%s?auth_app_id=%s' % (url_for('main.wxapp_setting'), auth_app_id))


@open.route('/wx/<string:appid>/receive_message')
def receive_message(appid):
    """接收公众号或小程序消息和事件推送"""
    current_app.logger.debug('Appid [%s]' % appid)
    signature = request.values.get('signature')
    timestamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')
    echostr = request.values.get('echostr')


@open.route('/wx/pay_notify', methods=['POST'])
def wxpay_notify():
    """微信支付异步通知"""
    current_app.logger.warn(request.data)
    data = WxPay.to_dict(request.data)
    # 微信支付初始化参数
    wx_pay = WxPay(
        wx_app_id=current_app.config['WXPAY_APP_ID'],
        wx_mch_id=current_app.config['WXPAY_MCH_ID'],
        wx_mch_key=current_app.config['WXPAY_MCH_SECRET'],
        wx_notify_url=current_app.config['WXPAY_NOTIFY_URL']
    )
    if not wx_pay.check(data):
        return wx_pay.reply('签名验证失败', False)
    # TODO:处理业务逻辑

    return wx_pay.reply('OK', True)


@open.route('/wx/service_message', methods=['GET', 'POST'])
def service_message():
    """接收客服消息"""
    current_app.logger.warn(request.values)

    signature = request.values.get('signature')
    time_stamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')

    token = '6e6d7bca7219d822cb08fb6c54d73584'
    encoding_aes_key = 'aE1coSGzvs23kiwxynIVnYVTjRBiR3M8XoWarIer302'

    wx_service = WxService(token=token, encoding_aes_key=encoding_aes_key)
    if wx_service.check_signature(time_stamp, nonce, signature):
        return 'SUCCESS'


@open.route('/wx/authorize')
def authorize():
    """跳转授权页"""
    pass


def _exchange_authorizer_token(auth_code):
    """使用授权码换取小程序的接口调用凭据和授权信息"""
    component_app_id = current_app.config['WX_APP_ID']
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
    # 发起请求
    wx_app_api = WxApp(component_app_id=component_app_id,
                       component_app_secret=current_app.config['WX_APP_SECRET'],
                       component_access_token=wx_token.access_token)
    result = wx_app_api.exchange_authorizer_token(auth_code)
    authorization_info = result.authorization_info

    authorizer_appid = authorization_info.authorizer_appid
    # 验证是否存在
    wx_authorizer = WxAuthorizer.query.filter_by(auth_app_id=authorizer_appid).first()
    if wx_authorizer is None:
        wx_authorizer = WxAuthorizer(
            master_uid=Master.master_uid(),
            auth_app_id=authorizer_appid,
            access_token=authorization_info.authorizer_access_token,
            refresh_token=authorization_info.authorizer_refresh_token,
            expires_in=authorization_info.expires_in,
            func_info=json.dumps(authorization_info.func_info)
        )
        db.session.add(wx_authorizer)
    else:
        wx_authorizer.access_token = authorization_info.authorizer_access_token
        wx_authorizer.refresh_token = authorization_info.authorizer_refresh_token
        wx_authorizer.expires_in = authorization_info.expires_in
        wx_authorizer.func_info = json.dumps(authorization_info.func_info)
        wx_authorizer.created_at = int(timestamp())

    db.session.commit()

    return authorizer_appid
