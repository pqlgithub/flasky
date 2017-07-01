# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import gettext
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Express

class ExpressForm(Form):
    name = StringField('Name', validators=[DataRequired("Name can't empty!")])
    # 联系人信息
    contact_name = StringField('Contact Name')
    contact_mobile = StringField('Contact Mobile')
    contact_phone = StringField('Contact Phone')
    description = TextAreaField('Description')

    def validate_name(self, filed):
        if Express.query.filter_by(name=filed.data).first():
            return ValidationError('Express [%s] already exist!' % filed.data)


class EditExpressForm(ExpressForm):

    def __init__(self, express, *args, **kwargs):
        super(EditExpressForm, self).__init__(*args, **kwargs)
        self.express = express

    def validate_name(self, filed):
        if filed.data != self.express.name and \
            Express.query.filter_by(name=filed.data).first():
            return ValidationError(gettext('Express name [%s] already exists.' % filed.data))


class ShipperForm(Form):
    warehouse_id = IntegerField('Warehouse')
    name = StringField('Name', validators=[DataRequired("Name can't empty!")])
    phone = StringField('Phone')
    mobile = StringField('Mobile')
    zipcode = IntegerField('Zipcode')
    # 始发地
    from_city = StringField('From City')
    province = StringField('Province')
    city = StringField('City')
    area = StringField('Area')
    address = StringField('Address')
