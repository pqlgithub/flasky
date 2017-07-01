# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import gettext
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import User, Role, Ability

class OrderForm(Form):
    serial_no = StringField('Serial No.')
    outside_target_id = StringField('Out Serial No.')
    store_id = IntegerField('From Store', validators=[DataRequired("From store can't empty!")])
    express_id = IntegerField('Express')
    warehouse_id = IntegerField('From Warehouse', validators=[DataRequired("From warehouse can't empty!")])
    pay_amount = DecimalField('Pay Amount')
    freight = DecimalField('Freight', default=0.00)
    remark = TextAreaField('Remark')

    buyer_name = StringField('Buyer Name', validators=[
        DataRequired('Buyer name is Null!'),
        Length(min=2, max=30, message='Name format is error!')])
    buyer_tel = StringField('Telephone', )
    buyer_phone = StringField('Mobile')
    buyer_zipcode = StringField('Zipcode')
    buyer_address = StringField('Address', validators=[
        DataRequired('Buyer address is Null!')])
    buyer_country = StringField('Country')
    buyer_province = StringField('Province')
    buyer_city = StringField('City')
    # 买家备注
    buyer_remark = TextAreaField('Buyer Remark')
