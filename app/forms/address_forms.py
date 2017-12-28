# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import StringField, IntegerField, RadioField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, ValidationError, InputRequired

from app.models import Country

class PlaceForm(Form):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired("Name can't empty!")])
    country_id = SelectField(lazy_gettext('Country'), choices=[], coerce=int)
    pid = IntegerField(lazy_gettext('For Parent'), default=0)
    sort_by= IntegerField(lazy_gettext('Sort By'))
    status = RadioField(lazy_gettext('Status'), choices=[
        (True, lazy_gettext('Enabled')),
        (False, lazy_gettext('Disabled'))
    ], coerce=bool, default=True)
    
class CountryForm(Form):
    name = StringField(lazy_gettext('Country Name'),
                       validators=[DataRequired(message=lazy_gettext('Country name cant empty!'))])
    en_name = StringField(lazy_gettext('English Name'),
                          validators=[DataRequired(message=lazy_gettext('Country name cant empty!'))])
    code = StringField(lazy_gettext('ISO Code'),
                             validators=[DataRequired(message=lazy_gettext('ISO Code (2) cant empty!'))])
    code2 = StringField(lazy_gettext('ISO Code (2)'))
    status = RadioField(lazy_gettext('Status'),
                         choices=[(1, 'Enabled'), (-1, 'Disabled')],
                         coerce=int)

    
    def validate_name(self, filed):
        if Country.query.filter_by(name=filed.data).first():
            return ValidationError(lazy_gettext('Country name [%s] already exists.' % filed.data))


class EditCountryForm(CountryForm):

    def __init__(self, country, *args, **kwargs):
        super(EditCountryForm, self).__init__(*args, **kwargs)
        self.country = country

    def validate_name(self, filed):
        if filed.data != self.country.name and \
            Country.query.filter_by(name=filed.data).first():
            return ValidationError(lazy_gettext('Country name [%s] already exists.' % filed.data))