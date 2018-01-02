# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Store
from ..constant import SUPPORT_PLATFORM

class StoreForm(Form):
    name = StringField(lazy_gettext('Channel Name'), validators=[DataRequired(message="Channel name can't empty!"), Length(2, 32)])
    platform = SelectField(lazy_gettext('Platform'), choices=[(pf['id'], pf['name']) for pf in SUPPORT_PLATFORM], coerce=int)
    operator_id = SelectField(lazy_gettext('Manager'), choices=[], coerce=int)
    type = SelectField(lazy_gettext('Type'), choices=[], coerce=int)
    status = RadioField(lazy_gettext('Status'),
                         choices=[(1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disabled'))],
                         coerce=int, default=1)
    description = TextAreaField(lazy_gettext('Description'))


class CurrencyForm(Form):
    title = StringField(lazy_gettext('Currency Title'), validators=[DataRequired(message=lazy_gettext('Currency title cant empty!'))])
    code = StringField(lazy_gettext('Code'), validators=[DataRequired(message=lazy_gettext('Currency code cant empty!'))])
    symbol_left = StringField(lazy_gettext('Symbol Left'))
    symbol_right = StringField(lazy_gettext('Symbol_right'))
    # 小数位
    decimal_place = IntegerField(lazy_gettext('Decimal Place'))
    value = FloatField(lazy_gettext('Value'))

    status = SelectField(lazy_gettext('Status'),
                         choices=[(1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disabled'))],
                         coerce=int)


class ClientForm(Form):
    name = StringField(lazy_gettext('App Name'),
                       validators=[DataRequired(message="App name can't empty!"), Length(2, 32)])
    limit_times = IntegerField(lazy_gettext('Limit Times'), default=5000)
    receive_url = StringField(lazy_gettext('Receive URL'), validators=[DataRequired(message="Receive URL can't empty!")])
    remark = TextAreaField(lazy_gettext('Remark'))