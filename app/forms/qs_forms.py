# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from flask_babelex import lazy_gettext
from wtforms.fields import IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired


class QuestionForm(Form):
    # pid = IntegerField(lazy_gettext('Question'))
    pid = IntegerField(lazy_gettext('问题类别'))
    # name = StringField(lazy_gettext('Question Name'), validators=[DataRequired()])
    name = StringField(lazy_gettext('问题名称'), validators=[DataRequired()])


class SolutionForm(Form):
    # question_id = IntegerField(lazy_gettext('Question Name'), validators=[DataRequired()])
    question_id = IntegerField(lazy_gettext('问题'), validators=[DataRequired()])
    # title = StringField(lazy_gettext('Title'), validators=[DataRequired()])
    title = StringField(lazy_gettext('标题'), validators=[DataRequired()])
    # content = TextAreaField(lazy_gettext('Content'), validators=[DataRequired()])
    content = TextAreaField(lazy_gettext('回答'), validators=[DataRequired()])