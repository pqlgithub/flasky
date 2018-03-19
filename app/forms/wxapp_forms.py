# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, FileField, IntegerField, FloatField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional


class WxPaymentForm(Form):
    auth_app_id = StringField(lazy_gettext('Authorize ID'), validators=[
        DataRequired(message="Authorize id can't empty!")])
    mch_id = StringField(lazy_gettext('MCH ID'), validators=[DataRequired(message="mch id can't empty!")])
    mch_key = StringField(lazy_gettext('MCH Key'), validators=[DataRequired(message="mch key can't empty!")])
    ssl_cert = FileField(lazy_gettext('SSL Cert'))
