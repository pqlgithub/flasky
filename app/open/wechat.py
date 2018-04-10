# -*- coding: utf-8 -*-
import json
from flask import current_app, request, redirect, url_for, render_template
import xml.etree.cElementTree as ET

from . import open
from .. import db, cache
from app.models import WxToken, WxAuthorizer, WxServiceMessage, WxMiniApp, WxVersion, Order, OrderStatus
from app.helpers import WXBizMsgCrypt, WxAppError, WxApp, WxPay, WxPayError, WxService, WxReply
from app.tasks import reply_wxa_service, sales_statistics
from app.utils import Master, custom_response, timestamp, status_response


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
            # 微信自动测试，设置至缓存, 15分钟，无需写入数据库
            if authorizer_app_id == current_app.config['WX_TEST_APP_ID']:
                cache.set('wx_%s_auth_code', authorizer_code, timeout=900)

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


@open.route('/wx/<string:appid>/receive_message', methods=['GET', 'POST'])
def receive_message(appid):
    """接收公众号或小程序消息和事件推送"""
    current_app.logger.debug('Appid [%s]' % appid)
    current_app.logger.warn(request.values)

    signature = request.values.get('signature')
    time_stamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')
    echostr = request.values.get('echostr')
    msg_signature = request.values.get('msg_signature')

    post_data = request.get_data()

    current_app.logger.warn('post data: %s' % post_data)

    # 解析内容活动to_user
    xml_tree = ET.fromstring(post_data)
    to_user = xml_tree.find('ToUserName').text

    current_app.logger.warn('To user name: %s' % to_user)

    token = current_app.config['WX_APP_TOKEN']
    encoding_aes_key = current_app.config['WX_APP_DES_KEY']
    auth_app_id = current_app.config['WX_APP_ID']

    # 解密接口
    decrypt = WXBizMsgCrypt(token, encoding_aes_key, auth_app_id)
    ret, decrypt_content = decrypt.DecryptMsg(post_data, msg_signature, time_stamp, nonce, 'service_message')

    # 更新
    current_app.logger.warn("decrypt content: %s" % decrypt_content)

    # 解密成功
    if ret == 0:
        # 解析内容
        xml_tree = ET.fromstring(decrypt_content)
        msg_type = xml_tree.find('MsgType').text

        if msg_type == 'text':  # 文本消息
            # 微信自动测试
            if to_user == current_app.config['WX_TEST_USERNAME']:
                content = xml_tree.find('Content').text
                if content.startswith('QUERY_AUTH_CODE'):
                    auth_info = content.split(':')
                    auth_code = auth_info[1]
                    reply_content = '{}_from_api'.format(auth_code)

                    # 使用授权码换取公众号的授权信息
                    auth_access_token = _exchange_authorizer_token(auth_code)
                    send_data = {
                        'touser': xml_tree.find('FromUserName').text,
                        'msgtype': 'text',
                        'text': {
                            'content': reply_content
                        }
                    }
                    try:
                        wx_reply = WxReply(access_token=auth_access_token)
                        wx_reply.send_message(data=send_data)
                    except WxAppError as err:
                        current_app.logger.warn('微信自动测试出错: %s' % err)

                    return 'success'
        elif msg_type == 'event':  # 事件消息
            event = xml_tree.find('Event').text
            if event == 'weapp_audit_success':  # 小程序审核通过
                success_time = xml_tree.find('SuccTime').text

                wx_version = WxVersion.query.filter_by(auth_app_id=appid).order_by(WxVersion.created_at.desc()).first()
                if wx_version:
                    wx_version.mark_audit_success(success_time)

                    db.session.commit()

            elif event == 'weapp_audit_fail':  # 小程序审核失败
                fail_reason = xml_tree.find('Reason').text
                fail_time = xml_tree.find('FailTime').text

                wx_version = WxVersion.query.filter_by(auth_app_id=appid).first()
                if wx_version:
                    wx_version.mark_audit_fail(fail_reason, fail_time)

                    db.session.commit()


@open.route('/wx/pay_notify', methods=['GET', 'POST'])
def wxpay_notify():
    """
    微信支付异步通知
    '<xml><appid><![CDATA[wx3cc0ea5d2c601f30]]></appid>\n<bank_type><![CDATA[LQT]]></bank_type>\n
    <cash_fee><![CDATA[20]]></cash_fee>\n<fee_type><![CDATA[CNY]]></fee_type>\n<is_subscribe><![CDATA[N]]>
    </is_subscribe>\n<mch_id><![CDATA[1490941762]]></mch_id>\n<nonce_str><![CDATA[Fx65c5WJfNElit1mPBKxCgp99v4Li80u]]>
    </nonce_str>\n<openid><![CDATA[o_PSJ5UIBFv-24mb06H3HMVZF6pY]]></openid>\n<out_trade_no><![CDATA[D18041049713605]]>
    </out_trade_no>\n<result_code><![CDATA[SUCCESS]]></result_code>\n<return_code><![CDATA[SUCCESS]]></return_code>\n
    <sign><![CDATA[936FA2945FD918A96D56848A823953C4]]></sign>\n<time_end><![CDATA[20180410142254]]></time_end>\n
    <total_fee>20</total_fee>\n<trade_type><![CDATA[NATIVE]]></trade_type>\n
    <transaction_id><![CDATA[4200000079201804105782996248]]></transaction_id>\n</xml>'
    """
    current_app.logger.debug(request.data)
    if not request.data:
        return status_response(False, {
            'code': 400,
            'message': '未收到请求参数'
        })

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

    # 处理业务逻辑
    if data['result_code'] == 'SUCCESS' and data['return_code'] == 'SUCCESS':
        rid = data['out_trade_no']
        pay_time = data['time_end']

        current_order = Order.query.filter_by(serial_no=rid).first()
        if current_order is None:
            current_app.logger.warn('订单[%s]不存在' % rid)
            return wx_pay.reply('订单不存在', False)

        if current_order.status == OrderStatus.PENDING_PAYMENT:  # 待支付
            current_order.mark_checked_status()
            current_order.payed_at = int(timestamp())

            # 触发异步任务
            sales_statistics.delay(current_order.id)

            db.session.commit()

    return wx_pay.reply('OK', True)


@open.route('/wx/service_message', methods=['GET', 'POST'])
def service_message():
    """接收客服消息"""
    current_app.logger.warn(request.values)

    signature = request.values.get('signature')
    time_stamp = request.values.get('timestamp')
    nonce = request.values.get('nonce')
    echostr = request.values.get('echostr')
    openid = request.values.get('openid')
    encrypt_type = request.values.get('encrypt_type')
    msg_signature = request.values.get('msg_signature')
    post_data = request.get_data()

    current_app.logger.warn('post data: %s' % post_data)

    # 解析内容活动to_user
    xml_tree = ET.fromstring(post_data)
    to_user = xml_tree.find('ToUserName').text

    current_app.logger.warn('To user name: %s' % to_user)

    # 微信自动测试
    if to_user != current_app.config['WX_TEST_USERNAME']:
        # 查询小程序信息
        wxapp = WxMiniApp.query.filter_by(user_name=to_user).first_or_404()
        if not wxapp:
            current_app.logger.warn("Wxapp %s isn't exist!" % to_user)
            return 'success'

        token = wxapp.service_token
        encoding_aes_key = wxapp.service_aes_key
        auth_app_id = wxapp.auth_app_id
    else:
        token = current_app.config['WX_APP_TOKEN']
        encoding_aes_key = current_app.config['WX_APP_DES_KEY']
        auth_app_id = current_app.config['WX_APP_ID']

    # 验证token
    if echostr:
        wx_service = WxService(token=token, encoding_aes_key=encoding_aes_key)
        if wx_service.check_signature(time_stamp, nonce, signature):
            return echostr

    # 解密接口
    decrypt = WXBizMsgCrypt(token, encoding_aes_key, auth_app_id)
    ret, decrypt_content = decrypt.DecryptMsg(post_data, msg_signature, time_stamp, nonce, 'service_message')

    # 解密成功
    if ret == 0:
        # 更新
        current_app.logger.warn("decrypt content: %s" % decrypt_content)
        # 解析内容
        xml_tree = ET.fromstring(decrypt_content)

        msg_type = xml_tree.find('MsgType').text

        if msg_type == 'text':  # 文本消息
            content = xml_tree.find('Content').text

            # 微信自动测试拦截，
            # 回应文本消息并最终触达粉丝：Content必须固定为：TESTCOMPONENT_MSG_TYPE_TEXT_callback
            if content.startswith('QUERY_AUTH_CODE'):
                auth_info = content.split(':')
                auth_code = auth_info[1]
                reply_content = '{}_from_api'.format(auth_code)

                # 使用授权码换取公众号的授权信息
                auth_access_token = _exchange_authorizer_token(auth_code)
                send_data = {
                    'touser': xml_tree.find('FromUserName').text,
                    'msgtype': 'text',
                    'text': {
                        'content': reply_content
                    }
                }
                try:
                    wx_reply = WxReply(access_token=auth_access_token)
                    wx_reply.send_message(data=send_data)
                except WxAppError as err:
                    current_app.logger.warn('微信自动测试出错: %s' % err)

                return 'success'
            elif content == 'TESTCOMPONENT_MSG_TYPE_TEXT':
                reply_content = 'TESTCOMPONENT_MSG_TYPE_TEXT_callback'
                wx_reply_message = WxServiceMessage(
                    master_uid=wxapp.master_uid,
                    auth_app_id=auth_app_id,
                    to_user=xml_tree.find('FromUserName').text,
                    from_user=xml_tree.find('ToUserName').text,
                    msg_type=msg_type,
                    create_time=xml_tree.find('CreateTime').text,
                    content=reply_content,
                    msg_id=xml_tree.find('MsgId').text,
                    type=2,
                    status=2
                )
                db.session.add(wx_reply_message)
                db.session.commit()

                # 异步任务，后台发送
                reply_wxa_service.apply_async(args=[wx_reply_message.id])

                return 'success'

            # 更新客服信息
            wx_service_message = WxServiceMessage(
                master_uid=wxapp.master_uid,
                auth_app_id=auth_app_id,
                to_user=xml_tree.find('ToUserName').text,
                from_user=xml_tree.find('FromUserName').text,
                msg_type=msg_type,
                create_time=xml_tree.find('CreateTime').text,
                content=content,
                msg_id=xml_tree.find('MsgId').text,
                type=1
            )
            db.session.add(wx_service_message)

            db.session.commit()
        elif msg_type == 'event':  # 进入会话事件
            event = xml_tree.find('Event').text
            reply_content = '{}from_callback'.format(event)  # 微信自动化测试所需
            wx_reply_message = WxServiceMessage(
                master_uid=wxapp.master_uid,
                auth_app_id=auth_app_id,
                to_user=xml_tree.find('FromUserName').text,
                from_user=xml_tree.find('ToUserName').text,
                msg_type=msg_type,
                create_time=xml_tree.find('CreateTime').text,
                content=reply_content,
                msg_id=xml_tree.find('MsgId').text,
                type=2,
                status=2
            )
            db.session.add(wx_reply_message)

            db.session.commit()

            # 异步任务，后台发送
            reply_wxa_service.apply_async(args=[wx_reply_message.id])
        else:
            pass

    return 'success'


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

    if authorizer_appid == current_app.config['WX_TEST_APP_ID']:  # 微信自动化测试，则无需更新数据库
        return authorization_info.authorizer_access_token

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
