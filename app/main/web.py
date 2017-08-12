# -*- coding: utf-8 -*-
from flask import g, session, current_app, request, redirect, url_for, render_template
from flask_login import current_user, login_required
from . import main
from .. import db, babel
from ..constant import SUPPORT_LANGUAGES
from ..utils import Master


@main.route('/')
@main.route('/index.html')
def web_index():
    return render_template('web/index.html',
                           active_menu='index')


@main.route('/features.html')
def features():
    return render_template('web/features.html',
                           active_menu='features')


@main.route('/pricing.html')
def pricing():
    return render_template('web/pricing.html',
                           active_menu='pricing')


@main.route('/about.html')
def about():
    return render_template('web/about.html')