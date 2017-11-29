# -*- coding: utf-8 -*-
from app import db
from app.models import Asset
from ..utils import timestamp

__all__ = [
    'Language'
]

class Language(db.Model):
    
    __tablename__ = 'languages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.String(5), unique=True, nullable=False)
    locale = db.Column(db.String(255), nullable=False)
    
    icon_id = db.Column(db.Integer, default=0)
    directory = db.Column(db.String(32))
    
    sort_order = db.Column(db.Integer, default=1)
    status = db.Column(db.SmallInteger, default=1)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def icon(self):
        """logo asset info"""
        return Asset.query.get(self.icon_id) if self.icon_id else None

    def __repr__(self):
        return '<Language {}>'.format(self.name)