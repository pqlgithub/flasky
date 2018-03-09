# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, optional


class BannerForm(Form):
    serial_no = StringField(lazy_gettext('Banner NO.'), validators=[DataRequired(message="Banner NO. can't empty!")])
    name = StringField(lazy_gettext('Banner Spot'), validators=[DataRequired(message="Banner spot can't empty!"),
                                                                Length(2, 32)])
    width = IntegerField(lazy_gettext('Width'), default=0)
    height = IntegerField(lazy_gettext('Height'), default=0)
    

class BannerImageForm(Form):
    title = StringField(lazy_gettext('Title'), validators=[DataRequired(message="Title can't empty!"), Length(2, 32)])
    link = StringField(lazy_gettext('Link Target'))
    type = RadioField(lazy_gettext('Link Type'), choices=[], coerce=int, default=1)
    spot_id = SelectField(lazy_gettext('Position'), choices=[], coerce=int, default=0)
    image_id = IntegerField(lazy_gettext('Image'), default=0)
    sort_order = IntegerField(lazy_gettext('Sort By'), default=0)
    description = TextAreaField(lazy_gettext('Description'))
    status = RadioField(lazy_gettext('Status'), choices=[(True, lazy_gettext('Enabled')),
                                                         (False, lazy_gettext('Disabled'))], coerce=bool, default=1)
