# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp


__all__ = [
    'WxTicket',
    'WxToken',
    'WxPreAuthCode',
    'WxAuthCode',
    'WxAuthorizer'
]


class WxTicket(db.Model):
    """微信第三方接口调用凭据,每隔10分钟定时推送component_verify_ticket"""

    __tablename__ = 'wx_tickets'

    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(20), index=True)
    info_type = db.Column(db.String(32))
    ticket = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxTicket {}>'.format(self.app_id)


class WxToken(db.Model):
    """
    微信第三方平台的下文中接口的调用凭据，也叫做令牌（component_access_token）。
    每个令牌是存在有效期（2小时）的，且令牌的调用不是无限制的，请第三方平台做好令牌的管理，在令牌快过期时（比如1小时50分）再进行刷新。
    """

    __tablename__ = 'wx_tokens'

    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(20), index=True)
    access_token = db.Column(db.String(200), unique=True, nullable=False)
    expires_in = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxToken {}>'.format(self.access_token)


class WxPreAuthCode(db.Model):
    """预授权码用于公众号或小程序授权时的第三方平台方安全验证"""

    __tablename__ = 'wx_pre_auth_codes'

    id = db.Column(db.Integer, primary_key=True)
    pre_auth_code = db.Column(db.String(100), unique=True, nullable=False)
    expires_in = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxPreAuthCode {}>'.format(self.pre_auth_code)


class WxAuthCode(db.Model):
    """授权码的获取，需要在用户在第三方平台授权页中完成授权流程后，在回调URI中通过URL参数提供给第三方平台方"""

    __tablename__ = 'wx_auth_codes'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    auth_code = db.Column(db.String(100), unique=True, nullable=False)
    expires_in = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxAuthCode {}>'.format(self.auth_code)


class WxAuthorizer(db.Model):
    """微信授权方信息"""

    __tablename__ = 'wx_authorizer'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    app_id = db.Column(db.String(20), index=True, nullable=False)
    access_token = db.Column(db.String(100), unique=True, nullable=False)
    refresh_token = db.Column(db.String(64), nullable=False)
    expires_in = db.Column(db.Integer, default=0)
    func_info = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxAuthorizer {}>'.format(self.app_id)


class WxAuthorizerInfo(db.Model):
    """授权方账号-小程序基本信息"""

    __tablename__ = 'wx_authorizer_info'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    app_id = db.Column(db.String(20), index=True, nullable=False)
    nick_name = db.Column(db.String(100), index=True, nullable=False)
    head_img = db.Column(db.String(100))
    # 小程序的原始ID
    user_name = db.Column(db.String(64))
    # 帐号介绍
    signature = db.Column(db.Text())
    # 小程序的主体名称
    principal_name = db.Column(db.String(64))
    # 授权方公众号类型，
    # 0代表订阅号，
    # 1代表由历史老帐号升级后的订阅号，
    # 2代表服务号
    service_type_info = db.Column(db.String(100))
    # 授权方认证类型:
    # -1代表未认证，0代表微信认证，1代表新浪微博认证，
    # 2代表腾讯微博认证，
    # 3代表已资质认证通过但还未通过名称认证，
    # 4代表已资质认证通过、还未通过名称认证，但通过了新浪微博认证，
    # 5代表已资质认证通过、还未通过名称认证，但通过了腾讯微博认证
    verify_type_info = db.Column(db.String(100))
    # open_store:是否开通微信门店功能
    # open_scan:是否开通微信扫商品功能
    # open_pay:是否开通微信支付功能
    # open_card:是否开通微信卡券功能
    # open_shake:是否开通微信摇一摇功能
    business_info = db.Column(db.String(100))
    qrcode_url = db.Column(db.String(100))
    # 可根据这个字段判断是否为小程序类型授权
    mini_program_info = db.Column(db.Text())
    # 小程序授权给开发者的权限集列表
    func_info = db.Column(db.Text(), nullable=False)

    created_at = db.Column(db.Integer, default=timestamp)
    update_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<WxAuthorizerInfo {}>'.format(self.app_id)

