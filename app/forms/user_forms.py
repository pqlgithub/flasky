# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField, FieldList
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional

from app.models import User, Role, Ability

class RoleForm(Form):
    name = StringField('Role Name', validators=[DataRequired(message="Role name can't empty!"), Length(2, 32)])
    title = StringField('Title')
    description = TextAreaField('Description')


class AbilityForm(Form):
    name = StringField('Ability Name', validators=[DataRequired(message="Ability name can't empty!")])

    def validate_name(self, filed):
        if Ability.query.filter_by(name=filed.data).first():
            return ValidationError('Ability [%s] already exist!' % filed.data)