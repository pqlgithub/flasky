# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Category, BUSINESS_MODE, DANGEROUS_GOODS_TYPES
from ..utils import Master
from ..constant import DEFAULT_REGIONS


class SupplierForm(Form):
    type = SelectField(lazy_gettext('Business Mode'), choices=[(mode[0], mode[2]) for mode in BUSINESS_MODE], coerce=str)
    short_name = StringField(lazy_gettext('Short Name'), validators=[DataRequired()])
    full_name = StringField(lazy_gettext('Full Name'), validators=[DataRequired()])
    start_date = StringField(lazy_gettext('Start date'))
    end_date = StringField(lazy_gettext('End date'))
    contact_name = StringField(lazy_gettext('Contact'))
    phone = StringField(lazy_gettext('Phone'))
    address = StringField(lazy_gettext('Address'))
    remark = TextAreaField(lazy_gettext('Remark'))


class BrandForm(Form):
    supplier_id = IntegerField(lazy_gettext('Supplier'))
    name = StringField(lazy_gettext('Brand Name'), validators=[DataRequired()])
    features = StringField(lazy_gettext('Features'))
    is_recommended = BooleanField(lazy_gettext('Is Recommended?'), default=False)
    description = TextAreaField(lazy_gettext('Description'))
    sort_order = IntegerField(lazy_gettext('Sort Order'))
    logo_id = IntegerField(lazy_gettext('Logo'), default=0)
    banner_id = IntegerField(lazy_gettext('Banner'), default=0)
    
    status = SelectField(lazy_gettext('Status'), choices=[
        (1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disabled'))
    ], coerce=int, default=-1)


class CategoryForm(Form):
    name = StringField(lazy_gettext('Category Name'), validators=[DataRequired()])
    sort_order = IntegerField(lazy_gettext('Sort Order'))
    pid = IntegerField(lazy_gettext('Parent'), default=0)
    description = TextAreaField(lazy_gettext('Description'))
    status = SelectField(lazy_gettext('Status'), choices=[
        (1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disabled'))
    ], coerce=int)


    def validate_name(self, field):
        """验证分类名称是否唯一"""
        if Category.query.filter_by(master_uid=Master.master_uid(), name=field.data).first():
            raise ValidationError(lazy_gettext('Category name is already exist!'))


class EditCategoryForm(CategoryForm):

    def __init__(self, category, *args, **kwargs):
        super(EditCategoryForm, self).__init__(*args, **kwargs)

        self.category = category

    def validate_name(self, field):
        """验证分类名称是否唯一"""
        if field.data != self.category.name and \
            Category.query.filter_by(master_uid=Master.master_uid(), name=field.data).first():
            raise ValidationError(lazy_gettext('Category name is already exist!'))


class ProductForm(Form):

    supplier_id = IntegerField(lazy_gettext('Supplier'))
    category_id = IntegerField(lazy_gettext('Category'))

    serial_no = StringField(lazy_gettext('Serial No.'), validators=[DataRequired()])
    name = StringField(lazy_gettext('Product Name'), validators=[DataRequired()])
    cover_id = IntegerField(lazy_gettext('Cover'), default=0)
    currency_id = SelectField(lazy_gettext('Currency'), choices=[], coerce=int)
    region_id = SelectField(lazy_gettext('Region'), choices=[(region['id'], region['name']) for region in DEFAULT_REGIONS], coerce=int)
    cost_price = FloatField(lazy_gettext('Cost Price'))
    sale_price = FloatField(lazy_gettext('Sale Price'))
    s_weight = FloatField(lazy_gettext('Weight'), default=0.0)
    s_length = FloatField(lazy_gettext('Length'), default=0.0)
    s_width = FloatField(lazy_gettext('Width'), default=0.0)
    s_height = FloatField(lazy_gettext('Height'), default=0.0)
    from_url = StringField(lazy_gettext('View Url'))
    status = SelectField(lazy_gettext('Status'), choices=[
        (1, lazy_gettext('Enabled')), (0, lazy_gettext('Disabled'))
    ], coerce=int)
    description = TextAreaField(lazy_gettext('Description'))

    # 报关信息
    dangerous_goods = RadioField(lazy_gettext('Dangerous Goods'), choices=DANGEROUS_GOODS_TYPES, coerce=str, default='N')
    local_name = StringField(lazy_gettext('Locale Name'))
    en_name = StringField(lazy_gettext('English Name'))
    d_weight = FloatField(lazy_gettext('Weight'), default=0.00)
    amount = FloatField(lazy_gettext('Amount'), default=0.00)
    customs_code = StringField(lazy_gettext('Customs Code'))


class ProductSkuForm(Form):
    serial_no = StringField(lazy_gettext('Serial No.'), validators=[DataRequired()])
    sku_cover_id = IntegerField(lazy_gettext('Cover'), default=0)
    id_code = StringField(lazy_gettext('Commodity Codes'))
    cost_price = FloatField(lazy_gettext('Cost Price'), default=0.00)
    sale_price = FloatField(lazy_gettext('Sale Price'), default=0.00)
    s_model = StringField(lazy_gettext('Mode'))
    s_color = StringField(lazy_gettext('Color'))
    s_weight = FloatField(lazy_gettext('Weight'), default=0.00)
    remark = TextAreaField(lazy_gettext('Remark'))