# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

class OrderForm(Form):
    serial_no = StringField(lazy_gettext('Serial No.'))
    outside_target_id = StringField(lazy_gettext('Out Serial No.'))
    store_id = SelectField(lazy_gettext('From Store'), choices=[], validators=[DataRequired("From store can't empty!")],
                           coerce=int)
    express_id = SelectField(lazy_gettext('Express'), choices=[], coerce=int)
    warehouse_id = SelectField(lazy_gettext('From Warehouse'), choices=[], validators=[DataRequired("From warehouse can't empty!")],
                               coerce=int)
    pay_amount = DecimalField(lazy_gettext('Pay Amount'))
    freight = DecimalField(lazy_gettext('Freight'), default=0.00)
    remark = TextAreaField(lazy_gettext('Remark'))

    buyer_name = StringField(lazy_gettext('Buyer Name'), validators=[
        DataRequired('Buyer name is Null!'),
        Length(min=2, max=30, message='Name format is error!')])
    buyer_tel = StringField(lazy_gettext('Telephone'))
    buyer_phone = StringField(lazy_gettext('Mobile'))
    buyer_zipcode = StringField(lazy_gettext('Zipcode'))
    buyer_address = StringField(lazy_gettext('Address'), validators=[
        DataRequired('Buyer address is Null!')])
    buyer_country = StringField(lazy_gettext('Country'))
    buyer_province = StringField(lazy_gettext('Province'))
    buyer_city = StringField(lazy_gettext('City'))
    # 买家备注
    buyer_remark = TextAreaField(lazy_gettext('Buyer Remark'))



class OrderExpressForm(Form):
    express_id = IntegerField(lazy_gettext('Express'))
    express_no = StringField(lazy_gettext('Express No.'))