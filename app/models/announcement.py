# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp


class Announcement(db.Model):
    """公告"""

    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)

    content = db.Column(db.Text, nullable=False)
    # 状态：是否发布，1、默认草稿；2、发布可见
    status = db.Column(db.SmallInteger, default=1)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<Announcement {}>'.format(self.id)
