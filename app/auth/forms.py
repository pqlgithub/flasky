# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.models import User


class LoginForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired()])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired()])
    remember_me = BooleanField(lazy_gettext('Remember me'), default=False)


class SignupForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(lazy_gettext('Username'), validators=[DataRequired(), Length(1, 64)])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField(lazy_gettext('Confirm password'), validators=[DataRequired()])

    # 中定义了以validate_ 开头且后面跟着字段名的方法，
	# 这个方法就和常规的验证函数一起调用

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(lazy_gettext('Username is already exist!'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(lazy_gettext('Email is already exist!'))