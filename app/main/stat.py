# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db

@main.route('/stats')
def stats():
    return render_template('stats/index.html')