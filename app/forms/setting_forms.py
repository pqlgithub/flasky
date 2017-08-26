# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Store
from ..constant import SUPPORT_PLATFORM

class StoreForm(Form):
    name = StringField(lazy_gettext('Store Name'), validators=[DataRequired(message="Store name can't empty!"), Length(2, 32)])
    platform = SelectField(lazy_gettext('Platform'), choices=[(pf['id'], pf['name']) for pf in SUPPORT_PLATFORM], coerce=int)
    operator_id = SelectField(lazy_gettext('Operator'), choices=[], coerce=int)
    status = SelectField(lazy_gettext('Status'),
                         choices=[(1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disabled'))],
                         coerce=int)
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
