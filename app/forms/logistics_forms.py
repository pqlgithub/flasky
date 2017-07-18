# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Express

class ExpressForm(Form):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired("Name can't empty!")])
    # 联系人信息
    contact_name = StringField(lazy_gettext('Contact Name'))
    contact_mobile = StringField(lazy_gettext('Contact Mobile'))
    contact_phone = StringField(lazy_gettext('Contact Phone'))
    description = TextAreaField(lazy_gettext('Description'))

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
            return ValidationError(lazy_gettext('Express name [%s] already exists.' % filed.data))


class ShipperForm(Form):
    warehouse_id = IntegerField(lazy_gettext('Warehouse'))
    name = StringField(lazy_gettext('Contact Name'), validators=[DataRequired("Name can't empty!")])
    phone = StringField(lazy_gettext('Phone'))
    mobile = StringField(lazy_gettext('Mobile'))
    zipcode = IntegerField(lazy_gettext('Zipcode'))
    # 始发地
    from_city = StringField(lazy_gettext('From City'))
    province = StringField(lazy_gettext('Province'))
    city = StringField(lazy_gettext('City'))
    area = StringField(lazy_gettext('Area'))
    address = StringField(lazy_gettext('Address'))
