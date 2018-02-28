# -*- coding: utf-8 -*-
from app import db
from .asset import Asset
from ..utils import timestamp
from ..helpers import MixGenId


__all__ = [
    'WxToken',
    'WxAuthCode',
    'WxAuthorizer',
    'WxMiniApp',
    'WxPayment',
    'WxTemplate'
]


class WxMiniApp(db.Model):
    """授权方账号-小程序基本信息"""

    __tablename__ = 'wx_mini_apps'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    # 生成编号
    serial_no = db.Column(db.String(32), unique=True, index=True, nullable=False)

    auth_app_id = db.Column(db.String(20), index=True, nullable=False)
    nick_name = db.Column(db.String(100), index=True, nullable=False)
    head_img = db.Column(db.String(200))
    # 模板ID
    template_id = db.Column(db.String(32))
    # 帐号介绍
    signature = db.Column(db.Text())
    # 小程序的原始ID
    user_name = db.Column(db.String(64))
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
    qrcode_url = db.Column(db.String(200))
    # 可根据这个字段判断是否为小程序类型授权
    mini_program_info = db.Column(db.Text())
    # 小程序授权给开发者的权限集列表
    func_info = db.Column(db.Text(), nullable=False)
    # 地理位置上报选项
    location_report = db.Column(db.SmallInteger, default=0)
    # 语音识别开关选项
    voice_recognize = db.Column(db.SmallInteger, default=0)
    # 多客服开关选项
    customer_service = db.Column(db.SmallInteger, default=0)

    # 状态: -1 禁用；0 默认；1 正常；
    status = db.Column(db.SmallInteger, default=0)

    # 默认值，语言、国家、币种
    default_country = db.Column(db.Integer, default=0)
    default_language = db.Column(db.Integer, default=0)
    default_currency = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, default=timestamp)
    update_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @staticmethod
    def make_unique_serial_no():
        serial_no = MixGenId.gen_shop_sn()
        if WxMiniApp.query.filter_by(serial_no=serial_no).first() is None:
            return serial_no
        while True:
            new_serial_no = MixGenId.gen_shop_sn()
            if WxMiniApp.query.filter_by(serial_no=new_serial_no).first() is None:
                break
        return new_serial_no

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'rid': self.serial_no,
            'auth_app_id': self.auth_app_id,
            'nick_name': self.nick_name,
            'user_name': self.user_name,
            'head_img': self.head_img,
            'signature': self.signature,
            'qrcode_url': self.qrcode_url,
            'status': self.status,
            'created_at': self.created_at
        }
        return json_obj

    def __repr__(self):
        return '<WxAuthorizerInfo {}>'.format(self.app_id)


class WxAuthorizer(db.Model):
    """微信小程序授权方"""

    __tablename__ = 'wx_authorizer'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    auth_app_id = db.Column(db.String(32), index=True, nullable=False)
    access_token = db.Column(db.String(200), unique=True, nullable=False)
    refresh_token = db.Column(db.String(200), nullable=False)
    expires_in = db.Column(db.Integer, default=0)
    func_info = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxAuthorizer {}>'.format(self.auth_app_id)


class WxPayment(db.Model):
    """小程序支付key与secret"""

    __tablename__ = 'wx_payments'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)

    auth_app_id = db.Column(db.String(32), index=True, nullable=False)
    # 商户号
    mch_id = db.Column(db.String(16), nullable=False)
    # 商户支付密钥
    mch_key = db.Column(db.String(64), nullable=False)
    # 商户证书路径
    ssl_key = db.Column(db.String(100))
    ssl_cert = db.Column(db.String(100))

    created_at = db.Column(db.Integer, default=timestamp)
    update_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<WxPayment {}>'.format(self.auth_app_id)


class WxTemplate(db.Model):
    """微信小程序模板"""

    __tablename__ = 'wx_templates'

    id = db.Column(db.Integer, primary_key=True)
    # 模板ID
    template_id = db.Column(db.String(32))
    name = db.Column(db.String(30), index=True, nullable=False)
    description = db.Column(db.String(200))
    # 封面图
    cover_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    # 更多附件Ids: 123, 253
    attachment = db.Column(db.String(200))
    # 被使用的次数
    used_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)
    update_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def cover(self):
        """cover asset info"""
        return Asset.query.get(self.cover_id) if self.cover_id else None

    def __repr__(self):
        return '<WxTemplate {}>'.format(self.template_id)


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


class WxAuthCode(db.Model):
    """授权码的获取，需要在用户在第三方平台授权页中完成授权流程后，在回调URI中通过URL参数提供给第三方平台方"""

    __tablename__ = 'wx_auth_codes'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    auth_app_id = db.Column(db.String(32), nullable=True)
    auth_code = db.Column(db.String(200), unique=True, nullable=False)
    expires_in = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxAuthCode {}>'.format(self.auth_code)


class WxTicket(db.Model):
    """
    微信第三方接口调用凭据,每隔10分钟定时推送component_verify_ticket
    已废除，采用Redis缓存实现
    """

    __tablename__ = 'wx_tickets'

    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(20), index=True)
    info_type = db.Column(db.String(32))
    ticket = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxTicket {}>'.format(self.app_id)


class WxPreAuthCode(db.Model):
    """
    预授权码用于公众号或小程序授权时的第三方平台方安全验证
    已废除，采用Redis缓存实现
    """

    __tablename__ = 'wx_pre_auth_codes'

    id = db.Column(db.Integer, primary_key=True)
    pre_auth_code = db.Column(db.String(100), unique=True, nullable=False)
    expires_in = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<WxPreAuthCode {}>'.format(self.pre_auth_code)
