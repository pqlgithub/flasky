# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from ..decorators import user_has

@main.route('/stats')
@login_required
@user_has('admin_reports')
def stats():
    return render_template('stats/index.html')