# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, IntegerField, FloatField, RadioField
from wtforms.validators import DataRequired,ValidationError


class CouponForm(Form):
    name = StringField(lazy_gettext('Coupon Name'))
    # 金额
    amount = FloatField(lazy_gettext('Coupon Amount'), default=1.00,
                        validators=[DataRequired("Coupon Amount can't empty!")])
    type = RadioField(lazy_gettext('Type'), choices=[
        (1, lazy_gettext('Standard')),
        (2, lazy_gettext('Minimum')),
        (3, lazy_gettext('Subtraction')),
    ], coerce=int, default=1)
    # 过期时间
    start_date = StringField(lazy_gettext('Start Date'))
    end_date = StringField(lazy_gettext('End Date'))
    min_amount = StringField(lazy_gettext('Min Amount'))
    reach_amount = StringField(lazy_gettext('Reach Amount'))
    product_rid = StringField(lazy_gettext('Limit Product'))
    status = RadioField(lazy_gettext('Status'), choices=[
        (1, lazy_gettext('Enabled')),
        (-1, lazy_gettext('Disabled'))
    ], coerce=int, default=1)
