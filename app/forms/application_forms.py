# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, IntegerField, FloatField, TextAreaField, BooleanField, SelectField, RadioField
from wtforms.validators import DataRequired,ValidationError
from ..constant import SERVICE_TYPES


class ApplicationForm(Form):
    name = StringField(lazy_gettext('Application Name'), validators=[DataRequired("Application Name can't empty!")])
    icon_id = IntegerField(lazy_gettext('Application Icon'))
    summary = TextAreaField(lazy_gettext('Summary'))
    type = SelectField(lazy_gettext('Type'), choices=[(st[0], st[1]) for st in SERVICE_TYPES], coerce=int)
    is_free = BooleanField(lazy_gettext('Is free'), default=True)
    # 收费价格
    sale_price = FloatField(lazy_gettext('Sale Price'))
    description = TextAreaField(lazy_gettext('Description'))
    remark = TextAreaField(lazy_gettext('Remark'))
    status = RadioField(lazy_gettext('Status'), choices=[
        (2, lazy_gettext('Enabled')),
        (1, lazy_gettext('Pending')),
        (-1, lazy_gettext('Disabled'))
    ], coerce=int, default=2)


class WxTemplateForm(Form):
    # 模板ID
    template_id = StringField(lazy_gettext('Template ID'), validators=[DataRequired("Template id can't empty!")])
    name = StringField(lazy_gettext('Name'), validators=[DataRequired("Name can't empty!")])
    description = TextAreaField(lazy_gettext('Description'))
    # 封面图
    cover_id = IntegerField(lazy_gettext('Template Cover'))
    # 更多附件Ids: 123, 253
    attachment = StringField(lazy_gettext('Template Cover'))
    # 状态: -1 禁用；1 默认；2 正常；
    status = RadioField(lazy_gettext('Status'), choices=[
        (2, lazy_gettext('Approved')),
        (1, lazy_gettext('Pending')),
        (-1, lazy_gettext('Disabled'))
    ], coerce=int, default=2)
