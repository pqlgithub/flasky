# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from ..constant import SUPPORT_PLATFORM
from ..utils import Master
from app.models import Client


class StoreForm(Form):
    name = StringField(lazy_gettext('Store Name'), validators=[DataRequired(message="Store name can't empty!"), Length(2, 32)])
    platform = SelectField(lazy_gettext('Platform'), choices=[(pf['id'], pf['name']) for pf in SUPPORT_PLATFORM], coerce=int)
    operator_id = SelectField(lazy_gettext('Manager'), choices=[], coerce=int)
    type = SelectField(lazy_gettext('Type'), choices=[], coerce=int)
    distribute_mode = RadioField(lazy_gettext('Distribute Products'), choices=[], coerce=int, default=1)
    is_private_stock = BooleanField(lazy_gettext('Set Private Stock'), default=False)
    status = RadioField(lazy_gettext('Status'),
                         choices=[(1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disable'))],
                         coerce=int, default=1)
    description = TextAreaField(lazy_gettext('Description'))


class CurrencyForm(Form):
    title = StringField(lazy_gettext('Currency Title'), validators=[DataRequired(message=lazy_gettext('Currency title cant empty!'))])
    code = StringField(lazy_gettext('Code'), validators=[DataRequired(message=lazy_gettext('Currency code cant empty!'))])
    symbol_left = StringField(lazy_gettext('Symbol Left'))
    symbol_right = StringField(lazy_gettext('Symbol_right'))
    # 小数位
    decimal_place = IntegerField(lazy_gettext('Decimal Place'))
    value = FloatField(lazy_gettext('Value'))

    status = SelectField(lazy_gettext('Status'),
                         choices=[(1, lazy_gettext('Enabled')), (-1, lazy_gettext('Disabled'))],
                         coerce=int)


class ClientForm(Form):
    name = StringField(lazy_gettext('App Name'),
                       validators=[DataRequired(message="App name can't empty!"), Length(2, 32)])
    store_id = SelectField(lazy_gettext('Relation Store'), choices=[], coerce=int)
    limit_times = IntegerField(lazy_gettext('Limit Times'), default=5000)
    receive_url = StringField(lazy_gettext('Receive URL'), validators=[DataRequired(message="Receive URL can't empty!")])
    remark = TextAreaField(lazy_gettext('Remark'))
    
    def validate_name(self, field):
        if Client.query.filter_by(name=field.data).first():
            raise ValidationError(lazy_gettext('App Name is already exist!'))


class EditClientForm(ClientForm):

    def __init__(self, client, *args, **kwargs):
        super(EditClientForm, self).__init__(*args, **kwargs)
        self.client = client

    def validate_name(self, field):
        """验证分类名称是否唯一"""
        if field.data != self.client.name and \
            Client.query.filter_by(master_uid=Master.master_uid(), name=field.data).first():
            raise ValidationError(lazy_gettext('App name is already exist!'))