# -*- coding: utf-8 -*-
from sqlalchemy import text, event
from flask_babelex import gettext, lazy_gettext
from app import db
from ..utils import timestamp
from .asset import Asset
from app.helpers import MixGenId

__all__ = [
    'Banner',
    'BannerImage',
    'LINK_TYPES'
]

# 链接类型
LINK_TYPES = [
    # 默认普通链接
    (1, lazy_gettext('Link Url')),
    (2, lazy_gettext('Product')),
    (3, lazy_gettext('Category')),
    (4, lazy_gettext('Brand')),
    # 专题
    (5, lazy_gettext('Topic'))
]


class Banner(db.Model):
    __tablename__ = 'banners'
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    serial_no = db.Column(db.String(12), index=True, nullable=False)
    
    name = db.Column(db.String(64), nullable=False)
    status = db.Column(db.SmallInteger, default=0)
    width = db.Column(db.Integer, default=0)
    height = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    # banner and images => 1 to N
    images = db.relationship(
        'BannerImage', backref='spot', lazy='dynamic'
    )
    
    @staticmethod
    def make_unique_sn():
        """生成品牌编号"""
        sn = MixGenId.gen_banner_sn()
        if Banner.query.filter_by(serial_no=sn).first() is None:
            return sn
    
        while True:
            new_sn = MixGenId.gen_banner_sn()
            if Banner.query.filter_by(serial_no=new_sn).first() is None:
                break
        return new_sn
    
    @staticmethod
    def on_before_insert(mapper, connection, target):
        # 自动生成用户编号
        target.serial_no = Banner.make_unique_sn()
    
    def __repr__(self):
        return '<Banner {}>'.format(self.name)


class BannerImage(db.Model):
    __tablename__ = 'banner_images'
    
    id = db.Column(db.Integer, primary_key=True)
    
    master_uid = db.Column(db.Integer, index=True, default=0)
    
    banner_id = db.Column(db.Integer, db.ForeignKey('banners.id'))
    
    title = db.Column(db.String(64), nullable=False)
    link = db.Column(db.String(255))
    image_id = db.Column(db.Integer, default=0)
    type = db.Column(db.SmallInteger, default=1)
    sort_order = db.Column(db.Integer, default=0)
    description = db.Column(db.String(200))
    status = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def image(self):
        """banner asset info"""
        return Asset.query.get(self.image_id) if self.image_id else Asset.default_banner()

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'rid': self.id,
            'title': self.title,
            'link': self.link,
            'image': self.image.view_url if self.image else '',
            'type': self.type,
            'sort_order': self.sort_order,
            'description': self.description,
            'status': self.status
        }
        return json_obj

    def __repr__(self):
        return '<BannerImage {}>'.format(self.title)
    
    
# 监听Banner事件
event.listen(Banner, 'before_insert', Banner.on_before_insert)