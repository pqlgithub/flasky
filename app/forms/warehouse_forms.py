# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm as Form
from flask_babelex import gettext
from wtforms.fields import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Warehouse, WarehouseShelve

class WarehouseForm(Form):
    name = StringField('Warehouse Name', validators=[DataRequired()])
    address = TextAreaField('Address')
    en_address = TextAreaField('En Address')
    description = TextAreaField('Description')

    username = StringField('Username')
    phone = StringField('Phone')
    email = StringField('Email')
    qq = StringField('QQ')

    type = RadioField('Warehouse Type', choices=Warehouse.wh_types(), coerce=int)
    is_default = BooleanField('Default Warehouse', default=False)
    status = SelectField('Status', choices=[
        (1, 'Enabled'), (-1, 'Disabled')
    ], coerce=int)


