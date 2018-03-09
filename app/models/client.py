# -*- coding: utf-8 -*-
import hashlib
from flask_babelex import gettext, lazy_gettext
from app import db
from app.models import Store
from ..utils import timestamp

__all__ = [
    'Client',
    'ClientStatus'
]


class ClientStatus:
    # 通过审核
    ENABLED = 2
    # 等待审核
    PENDING = 1
    # 拒绝
    DISABLED = -1


# 应用的状态
CLIENT_STATUS = [
    (ClientStatus.ENABLED, lazy_gettext('Approved'), 'success'),
    (ClientStatus.PENDING, lazy_gettext('Pending'), 'success'),
    (ClientStatus.DISABLED, lazy_gettext('Disabled'), 'danger')
]


class Client(db.Model):
    """应用列表"""
    
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, default=0)
    
    name = db.Column(db.String(32), unique=True, nullable=False)
    # 关联渠道ID
    store_id = db.Column(db.Integer, default=0)
    
    app_key = db.Column(db.String(20), unique=True, nullable=False)
    app_secret = db.Column(db.String(40), nullable=False)
    
    # 每日API调用上限
    limit_times = db.Column(db.Integer, default=5000)
    # 信息推送接收URL
    receive_url = db.Column(db.String(200), nullable=True)
    # 备注
    remark = db.Column(db.String(140), nullable=True)
    # IP 白名单
    white_list = db.Column(db.Text, nullable=True)
    # 审核状态
    status = db.Column(db.SmallInteger, default=0)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def status_label(self):
        for s in CLIENT_STATUS:
            if s[0] == self.status:
                return s

    @property
    def store(self):
        """获取关联渠道"""
        return Store.query.get(self.store_id) if self.store_id else None
    
    @staticmethod
    def check_api_sign(args, app_secret):
        """
        验证API数字签名
        
        签名算法：
        1、将app_key,timestamp,nonce_str三个参数字典排序
        2、将三个参数字符串拼接成一个字符串+app_secret进行sha1加密
        3、加密后的字符串即为signature

        :param args: 认证参数
        :param app_secret: 验证密钥
        :return: 是否签名成功
        """
        ret = {
            'app_key': args['app_key'],
            'timestamp': args['timestamp'],
            'nonce_str': args['nonce_str']
        }
        
        tmp_str = '&'.join(['%s=%s' % (key.lower(), ret[key]) for key in sorted(ret)])
        
        sign = hashlib.sha1(tmp_str.encode('utf-8') + app_secret.encode('utf-8')).hexdigest()
        
        return sign == args['sign']

    def __repr__(self):
        return '<Client {}>'.format(self.id)
