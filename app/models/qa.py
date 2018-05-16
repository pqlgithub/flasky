# -*- coding: utf-8 -*-
from app import db
from ..utils import timestamp

__all__ = [
    'Question',
    'Solution'
]


class Question(db.Model):
    """问题类别"""

    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    pid = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<Question {}>'.format(self.name)

    @property
    def p_name(self):
        if self.pid > 0:
            question = Question.query.get(self.pid)
            return question.name
        else:
            return ''

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'pid': self.pid
        }


class Solution(db.Model):
    """问题的解决方案"""

    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)

    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))

    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    # 有用的数量
    useful_count = db.Column(db.Integer, default=0)
    # 无用的数量
    useless_count = db.Column(db.Integer, default=0)

    # 无用的原因
    # 描述不清楚
    cause_describe = db.Column(db.Integer, default=0)
    # 产品不满意
    cause_product = db.Column(db.Integer, default=0)
    # 内容不正确
    cause_content_err = db.Column(db.Integer, default=0)
    # 操作不当
    cause_operation = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<Solution {}>'.format(self.id)

    @property
    def question_name(self):
        question = Question.query.get(self.question_id)
        return question.name

    def to_json(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'question_name': self.question_name,
            'title': self.title,
            'content': self.content
        }