# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError, Email

from app.models import User, Role, Ability
from ..constant import SUPPORT_COUNTRIES, SUPPORT_CURRENCIES, SUPPORT_LANGUAGES, SUPPORT_DOMAINS


class SiteForm(Form):
    company_name = StringField(lazy_gettext('Company Name'),
                               validators=[DataRequired(message=lazy_gettext("Company name can't empty!")), Length(2, 32)])
    company_abbr = StringField(lazy_gettext('Company Abbreviation'),
                               validators=[DataRequired(message=lazy_gettext("Company Abbreviation can't empty!")), Length(1, 10)])

    country = SelectField(lazy_gettext('Country'), choices=[(c[1], c[2]) for c in SUPPORT_COUNTRIES], coerce=str)
    locale = SelectField(lazy_gettext('Default Language'), choices=[(l[1], l[2]) for l in SUPPORT_LANGUAGES], coerce=str)
    currency_id = SelectField(lazy_gettext('Default Currency'), choices=[], coerce=int)
    domain = SelectField(lazy_gettext('Domain'), choices=SUPPORT_DOMAINS, coerce=int)
    description = TextAreaField(lazy_gettext('Description'))


class UserForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(lazy_gettext('Username'), validators=[DataRequired(), Length(1, 64)])
    password = PasswordField(lazy_gettext('Password'),
                             validators=[DataRequired(), EqualTo('password2', message=lazy_gettext('Passwords must match'))])
    password2 = PasswordField(lazy_gettext('Confirm password'), validators=[DataRequired()])

    # 中定义了以validate_ 开头且后面跟着字段名的方法
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(lazy_gettext('Username is already exist!'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(lazy_gettext('Email is already exist!'))


class RoleForm(Form):
    name = StringField(lazy_gettext('Role Name'), validators=[DataRequired(message="Role name can't empty!"), Length(2, 32)])
    title = StringField(lazy_gettext('Title'))
    description = TextAreaField(lazy_gettext('Description'))


class AbilityForm(Form):
    name = StringField(lazy_gettext('Ability Name'), validators=[DataRequired(message="Ability name can't empty!")])
    title = StringField(lazy_gettext('Ability Title'), validators=[DataRequired(message="Ability title can't empty!")])

    def validate_name(self, filed):
        if Ability.query.filter_by(name=filed.data).first():
            return ValidationError('Ability [%s] already exist!' % filed.data)


class PasswdForm(Form):
    password = PasswordField(lazy_gettext('Password'),
                             validators=[DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField(lazy_gettext('Confirm password'), validators=[DataRequired()])


class PreferenceForm(Form):
    locale = SelectField(lazy_gettext('Default Language'), choices=[(l[1], l[2]) for l in SUPPORT_LANGUAGES],
                         coerce=str)
