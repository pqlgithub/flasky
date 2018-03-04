# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, FloatField, TextAreaField, PasswordField, SelectField
from wtforms.validators import DataRequired,ValidationError


class H5mallForm(Form):
    name = StringField(lazy_gettext('Shop Name'), validators=[DataRequired("Shop Name can't empty!")])
    site_domain = StringField(lazy_gettext('Shop Domain'))
    description = TextAreaField(lazy_gettext('Description'))
