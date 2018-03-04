# -*- coding: utf-8 -*-
from flask import render_template
from . import site


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
