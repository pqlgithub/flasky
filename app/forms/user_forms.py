# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError, Email

from app.models import User, Role, Ability
from ..constant import SUPPORT_COUNTRIES, SUPPORT_CURRENCIES, SUPPORT_LANGUAGES, SUPPORT_DOMAINS

class SiteForm(Form):
    company_name = StringField('Company Name', validators=[DataRequired(message="Company name can't empty!"), Length(2, 32)])
    company_abbr = StringField('Company Abbreviation', validators=[DataRequired(message="Company Abbreviation can't empty!"), Length(1, 10)])

    country = SelectField('Country', choices=[(c[1], c[2]) for c in SUPPORT_COUNTRIES], coerce=str)
    locale = SelectField('Language', choices=[(l[1], l[2]) for l in SUPPORT_LANGUAGES], coerce=str)
    currency = SelectField('Currency', choices=[(c[1], c[1]) for c in SUPPORT_CURRENCIES], coerce=str, default='CNY')
    domain = SelectField('Domain', choices=SUPPORT_DOMAINS, coerce=int)
    description = TextAreaField('Description')


class UserForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])

    # 中定义了以validate_ 开头且后面跟着字段名的方法，
	# 这个方法就和常规的验证函数一起调用

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(gettext('Username is already exist!'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email is already exist!')


class RoleForm(Form):
    name = StringField('Role Name', validators=[DataRequired(message="Role name can't empty!"), Length(2, 32)])
    title = StringField('Title')
    description = TextAreaField('Description')


class AbilityForm(Form):
    name = StringField('Ability Name', validators=[DataRequired(message="Ability name can't empty!")])
    title = StringField('Ability Title', validators=[DataRequired(message="Ability title can't empty!")])

    def validate_name(self, filed):
        if Ability.query.filter_by(name=filed.data).first():
            return ValidationError('Ability [%s] already exist!' % filed.data)