# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import gettext
from wtforms.fields import StringField, TextAreaField, IntegerField, DateField, DecimalField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Purchase, Warehouse, Supplier


class PurchaseForm(Form):

    warehouse_id = IntegerField('Warehouse', validators=[DataRequired()])
    supplier_id = IntegerField('Supplier', validators=[DataRequired()])
    freight = DecimalField('Freight', default=0.00)
    extra_charge = DecimalField('Extra Charge', default=0.00)
    arrival_date = DateField('Arrival Date')
    description = TextAreaField('Description')


class PurchaseExpressForm(Form):
    express_name = StringField('Express Name')
    express_no = TextAreaField('Express No.')
