# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from app.models import Order
from ..utils import Master

@main.route('/')
@main.route('/index')
@login_required
def index():
    top_orders = Order.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').limit(10).all()

    return render_template('index.html',
                           top_orders=top_orders)