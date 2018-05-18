# -*- coding: utf-8 -*-
from flask import render_template, current_app
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


@site.route('/qa.html')
def qa():
    questions = Question.query.filter_by(pid=0).all()
    for question in questions:
        question.sub_questions = Question.query.filter_by(pid=question.id).all()

    return render_template('web/questions.html',
                           active_menu='qa',
                           questions=questions)