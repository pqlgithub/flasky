# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, TextAreaField, IntegerField, DateField, DecimalField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

class PurchaseForm(Form):

    warehouse_id = IntegerField(lazy_gettext('Warehouse'), validators=[DataRequired()])
    supplier_id = IntegerField(lazy_gettext('Supplier'), validators=[DataRequired()])
    freight = DecimalField(lazy_gettext('Freight'), default=0.00)
    extra_charge = DecimalField(lazy_gettext('Extra Charge'), default=0.00)
    arrival_date = DateField(lazy_gettext('Arrival Date'))
    description = TextAreaField(lazy_gettext('Description'))


class PurchaseExpressForm(Form):
    express_name = StringField(lazy_gettext('Express Name'))
    express_no = TextAreaField(lazy_gettext('Express No.'))
