# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, IntegerField, FloatField, RadioField
from wtforms.validators import DataRequired,ValidationError


class BonusForm(Form):
    # 红包金额
    amount = FloatField(lazy_gettext('Bonus Amount'), default=2.00, validators=[DataRequired("Bonus Amount can't empty!")])
    # 设置数量
    quantity = IntegerField(lazy_gettext('Bonus Quantity'), default=1)
    # 过期时间
    expired_at = StringField(lazy_gettext('Expired Date'))
    min_amount = StringField(lazy_gettext('Min Amount'))
    xname = StringField(lazy_gettext('Remark'))
    product_rid = StringField(lazy_gettext('Limit Product'))
    status = RadioField(lazy_gettext('Status'), choices=[
        (1, lazy_gettext('Enabled')),
        (-1, lazy_gettext('Disabled'))
    ], coerce=int, default=1)
