# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm as Form
from flask_babelex import gettext
from wtforms.fields import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Product, Supplier, BUSINESS_MODE, DANGEROUS_GOODS_TYPES

class SupplierForm(Form):
    type = SelectField('Business Mode', choices=BUSINESS_MODE, coerce=str)
    name = StringField('Short Name', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    start_date = StringField('Start date')
    end_date = StringField('End date')
    contact_name = StringField('Contact')
    phone = StringField('Phone')
    address = StringField('Address')
    remark = TextAreaField('Remark')


class CategoryForm(Form):
    name = StringField('Category Name', validators=[DataRequired()])
    sort_order = IntegerField(gettext('Sort Order'))
    pid = IntegerField(gettext('Parent'), default=0)
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[
        (1, 'Enabled'), (-1, 'Disabled')
    ], coerce=int)


class ProductForm(Form):

    supplier_id = IntegerField('Supplier')
    category_id = IntegerField('Category')

    serial_no = StringField('Serial No.', validators=[DataRequired()])
    name = StringField('Product Name', validators=[DataRequired()])
    cover_id = IntegerField('Cover', default=0)
    cost_price = FloatField('Cost Price')
    sale_price = FloatField('Sale Price')
    s_weight = FloatField('Weight', default=0.0)
    s_length = FloatField('Length', default=0.0)
    s_width = FloatField('Width', default=0.0)
    s_height = FloatField('Height', default=0.0)
    from_url = StringField('View Url')
    status = SelectField('Status', choices=[
        (1, 'Enabled'), (-1, 'Disabled')
    ], coerce=int)
    description = TextAreaField('Description')

    # 报关信息
    dangerous_goods = RadioField('Dangerous Goods', choices=DANGEROUS_GOODS_TYPES, coerce=str, default='N')
    local_name = StringField('Locale Name')
    en_name = StringField('English Name')
    d_weight = FloatField('Weight', default=0.00)
    amount = FloatField('Amount', default=0.00)
    customs_code = StringField('Customs Code')


class ProductSkuForm(Form):
    serial_no = StringField('Serial No.', validators=[DataRequired()])
    sku_cover_id = IntegerField('Cover', default=0)
    cost_price = FloatField('Cost Price', default=0.00)
    sale_price = FloatField('Sale Price', default=0.00)
    s_model = StringField('Model')
    s_weight = FloatField('Weight', default=0.00)
    remark = TextAreaField('Remark')