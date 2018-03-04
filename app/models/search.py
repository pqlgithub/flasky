# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp


__all__ = [
    'SearchHistory'
]


class SearchHistory(db.Model):
    """搜索历史记录"""

    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)

    query_word = db.Column(db.String(50), index=True)
    total_count = db.Column(db.Integer, default=0)
    # 搜索次数
    search_times = db.Column(db.Integer, default=1)
    search_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def to_json(self):
        json_obj = {
            'query_word': self.query_word,
            'total_count': self.total_count,
            'search_times': self.search_times,
            'search_at': self.search_at
        }
        return json_obj

    def __repr__(self):
        return '<SearchHistory {}>'.format(self.keyword)
