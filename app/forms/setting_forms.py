# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import Store
from ..constant import SUPPORT_PLATFORM

class StoreForm(Form):
    name = StringField(lazy_gettext('Store Name'), validators=[DataRequired(message="Store name can't empty!"), Length(2, 32)])
    platform = SelectField(lazy_gettext('Platform'), choices=[(pf['id'], pf['name']) for pf in SUPPORT_PLATFORM], coerce=int)
