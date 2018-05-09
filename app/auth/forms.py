# -*- coding: utf-8 -*-
from flask import session
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from app.models import User
from app.constant import AREACODE


class LoginForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired()])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired()])
    remember_me = BooleanField(lazy_gettext('Remember me'), default=False)


class LoginErrorForm(LoginForm):
    """多次登录失败"""
    verifycode = StringField(validators=[DataRequired()])

    def validate_verifycode(self, field):
        verifycode = session.get('verifycode')
        if field.data.upper() != verifycode.upper():
            raise ValidationError(lazy_gettext('验证码不正确'))


class ResetPasswordFrom(Form):
    """重置密码"""
    areacode = SelectField(validators=[DataRequired()], render_kw={'id': 'areacode'})
    email = StringField(lazy_gettext('Email'),
                        validators=[DataRequired(), Regexp(regex="^1\d{10}$")])
    phoneverifycode = StringField(validators=[DataRequired(), Regexp(regex="^\d{4}$")])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(ResetPasswordFrom, self).__init__(*args, **kwargs)
        self.areacode.choices = [(i[2],i[2]) for i in AREACODE]

    # 中定义了以validate_ 开头且后面跟着字段名的方法
    def validate_phoneverifycode(self, field):
        phoneverifycode = session.get('phoneverifycode')

        if field.data != phoneverifycode:
            raise ValidationError(lazy_gettext('验证码不正确'))

    def validate_email(self, field):
        phonenum = session.get('phonenum')

        if field.data != phonenum:
            print('field.data',field.data)
            print('phonenum',phonenum)
            print('手机号不匹配')
            raise ValidationError(lazy_gettext('手机号不匹配。'))


class SignupForm(ResetPasswordFrom):
    """注册"""
    verifycode = StringField(validators=[DataRequired()])

    # 中定义了以validate_ 开头且后面跟着字段名的方法
    # def validate_email(self, field):
    #     if User.query.filter_by(email=field.data).first():
    #         raise ValidationError(lazy_gettext('Email is already exist!'))

    def validate_verifycode(self, field):
        verifycode = session.get('verifycode')

        if field.data.upper() != verifycode.upper():
            raise ValidationError(lazy_gettext('验证码不正确'))


