# -*- coding: utf-8 -*-

from wtforms.validators import ValidationError

class Unique(object):
    """自定义是否唯一的验证函数"""

    def __init__(self, model, field, message=u'该内容已经存在。'):
        self.model = model
        self.field = field
        self.message = message


    def __call__(self, form, field):
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            raise ValidationError(self.message)