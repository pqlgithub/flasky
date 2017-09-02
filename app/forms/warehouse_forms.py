# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Warehouse, WarehouseShelve

class WarehouseForm(Form):
    name = StringField(lazy_gettext('Warehouse Name'), validators=[DataRequired()])
    address = TextAreaField(lazy_gettext('Address'))
    en_address = TextAreaField(lazy_gettext('En Address'))
    description = TextAreaField(lazy_gettext('Description'))

    currency_id = SelectField(lazy_gettext('Currency'), choices=[], coerce=int)

    username = StringField(lazy_gettext('Contact Username'))
    phone = StringField(lazy_gettext('Phone'))
    email = StringField(lazy_gettext('Email'))
    qq = StringField(lazy_gettext('QQ'))

    type = RadioField(lazy_gettext('Warehouse Type'), choices=Warehouse.wh_types(), coerce=int)
    is_default = BooleanField(lazy_gettext('Default Warehouse'), default=False)
    status = SelectField(lazy_gettext('Status'), choices=[
        (1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disabled'))
    ], coerce=int)


