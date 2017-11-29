# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp

__all__ = [
    'Banner',
    'BannerImage'
]


class Banner(db.Model):
    __tablename__ = 'banners'
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    
    name = db.Column(db.String(64), nullable=False)
    status = db.Column(db.SmallInteger, default=0)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    def __repr__(self):
        return '<Banner {}>'.format(self.name)


class BannerImage(db.Model):
    __tablename__ = 'banner_images'
    
    id = db.Column(db.Integer, primary_key=True)
    
    master_uid = db.Column(db.Integer, index=True, default=0)
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'))
    
    banner_id = db.Column(db.Integer, db.ForeignKey('banners.id'))
    
    title = db.Column(db.String(64), nullable=False)
    link = db.Column(db.String(255))
    image = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)
    description = db.Column(db.String(200))

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    
    
    def __repr__(self):
        return '<BannerImage {}>'.format(self.title)