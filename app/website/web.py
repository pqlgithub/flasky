# -*- coding: utf-8 -*-
from flask import render_template
from . import site

from app.models import Question


@site.route('/')
@site.route('/index.html')
def web_index():
    return render_template('web/index.html',
                           active_menu='index')


@site.route('/features.html')
def features():
    return render_template('web/features.html',
                           active_menu='features')


@site.route('/pricing.html')
def pricing():
    return render_template('web/pricing.html',
                           active_menu='pricing')


@site.route('/about.html')
def about():
    return render_template('web/about.html')


@site.route('/questions.html')
def questions():
    questions = Question.query.filter_by(pid=0).all()
    return render_template('web/questions.html',
                           active_menu='questions',
                           questions=questions)