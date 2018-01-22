# -*- coding: utf-8 -*-
from flask import current_app
from app import db, uploader
from ..utils import timestamp
from app.helpers import Dictate


__all__ = [
    'Directory',
    'Asset'
]


class Directory(db.Model):
    """Directory of the assets"""
    __tablename__ = 'directories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    parent_id = db.Column(db.Integer, default=0)
    top = db.Column(db.SmallInteger, default=0)
    type = db.Column(db.SmallInteger, default=1)
    is_default = db.Column(db.Boolean, default=False)

    # directory and asset, 1 to N
    assets = db.relationship(
        'Asset', backref='directory', lazy='dynamic'
    )

    def __repr__(self):
        return '<Directory {}>'.format(self.name)


class Asset(db.Model):
    """Asset table.(image、file、video、pdf)"""
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)

    directory_id = db.Column(db.Integer, db.ForeignKey('directories.id'))

    filepath = db.Column(db.String(128), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Float, nullable=True)
    size = db.Column(db.Float, nullable=True)
    width = db.Column(db.Integer, default=0)
    height = db.Column(db.Integer, default=0)
    mime = db.Column(db.String(64), nullable=True)
    type = db.Column(db.SmallInteger, default=1)

    is_default = db.Column(db.Boolean, default=False)

    state = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def view_url(self):
        proto = 'http://'
        if current_app.config['FLASKS3_USE_HTTPS']:
            proto = 'https://'

        if not current_app.config['DEBUG']:
            url = '{}{}/{}'.format(
                proto,
                current_app.config['THUMB_CDN_DOMAIN'],
                self.filepath) if not self.is_default else '{}'.format(
                self.filepath)
        else:
            url = uploader.url(
                self.filepath) if not self.is_default else '{}'.format(
                self.filepath)

        return url

    @staticmethod
    def default_logo():
        """默认图-Logo"""
        return Dictate({
            'view_url': 'http://127.0.0.1:5000/static/img/no_img100x100.png'
        })

    @staticmethod
    def default_banner():
        """默认图-Banner"""
        return Dictate({
            'view_url': '/static/img/no_img100x100.png'
        })

    def __repr__(self):
        return '<Asset {}>'.format(self.filepath)

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_asset = {
            'id': self.id,
            'view_url': self.view_url,
            'filepath': self.filepath,
            'filename': self.filename,
            'created_at': self.created_at
        }
        return json_asset
