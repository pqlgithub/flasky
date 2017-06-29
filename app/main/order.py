# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from ..decorators import user_has, user_is


@main.route('/orders')
#@user_has('view_orders')
def show_orders():
    return render_template('order/show_list.html')


@main.route('/orders/create', methods=['GET', 'POST'])
#@user_is('admin')
def create_order():
    return render_template('order/create_and_edit.html')
