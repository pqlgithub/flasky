# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, FloatField, TextAreaField, PasswordField, SelectField
from wtforms.validators import DataRequired,ValidationError

from app.models import Customer

class CustomerForm(Form):
    name = StringField(lazy_gettext('Customer Name'), validators=[DataRequired("Customer Name can't empty!")])
    sn = StringField(lazy_gettext('Customer Code'), validators=[DataRequired("Customer Code can't empty!")])

    grade_id = SelectField(lazy_gettext('Customer Grade'), choices=[], coerce=int)
    
    # 联系人信息
    province = StringField(lazy_gettext('Province'))
    city = StringField(lazy_gettext('City'))
    area = StringField(lazy_gettext('Area'))
    street_address = StringField(lazy_gettext('Street address'))
    zipcode = StringField(lazy_gettext('Zipcode'))
    mobile = StringField(lazy_gettext('Mobile'), validators=[DataRequired("Mobile can't empty!")])
    phone = StringField(lazy_gettext('Phone'))
    email = StringField(lazy_gettext('Email'))
    qq = StringField(lazy_gettext('QQ'))
    
    # 设置登录账号与密码
    customer_account = StringField(lazy_gettext('Customer Account'), validators=[DataRequired("Customer Account can't empty!")])
    customer_pwd = PasswordField(lazy_gettext('Customer Password'), validators=[DataRequired("Customer Password can't empty!")])
    repeat_pwd = PasswordField(lazy_gettext('Confirmed Password'), validators=[DataRequired("Confirmed Password can't empty!")])
    
    def validate_sn(self, field):
        """验证分类名称是否唯一"""
        if Customer.query.filter_by(sn=field.data).first():
            raise ValidationError(lazy_gettext('Customer Code is already exist!'))
        
        
class CustomerEditForm(Form):
    name = StringField(lazy_gettext('Customer Name'), validators=[DataRequired("Customer Name can't empty!")])
    grade_id = SelectField(lazy_gettext('Customer Grade'), choices=[], coerce=int)

    # 联系人信息
    province = StringField(lazy_gettext('Province'))
    city = StringField(lazy_gettext('City'))
    area = StringField(lazy_gettext('Area'))
    street_address = StringField(lazy_gettext('Street address'))
    zipcode = StringField(lazy_gettext('Zipcode'))
    mobile = StringField(lazy_gettext('Mobile'), validators=[DataRequired("Mobile can't empty!")])
    phone = StringField(lazy_gettext('Phone'))
    email = StringField(lazy_gettext('Email'))
    qq = StringField(lazy_gettext('QQ'))
    
    
class CustomerGradeForm(Form):
    name = StringField(lazy_gettext('Grade Name'), validators=[DataRequired("Grade Name can't empty!")])
    

class DiscountTempletForm(Form):
    name = StringField(lazy_gettext('Discount Name'), validators=[DataRequired("Discount Name can't empty!")])
    default_discount = FloatField(lazy_gettext('Default Discount'))
    # 计算方式
    type = SelectField(lazy_gettext('By Type'), choices=[], coerce=int)
    description = TextAreaField(lazy_gettext('Description'))
    
    
class DiscountTempletEditForm(Form):
    name = StringField(lazy_gettext('Discount Name'), validators=[DataRequired("Discount Name can't empty!")])
    default_discount = FloatField(lazy_gettext('Default Discount'))
    description = TextAreaField(lazy_gettext('Description'))
    