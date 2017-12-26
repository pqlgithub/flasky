# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, IntegerField, FloatField, TextAreaField, BooleanField, SelectField
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
    status = SelectField(lazy_gettext('Status'), choices=[
        (2, lazy_gettext('Enabled')),
        (1, lazy_gettext('Pending')),
        (-1, lazy_gettext('Disabled'))
    ], coerce=int)

