# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from app.models import Order
from ..utils import Master
from ..decorators import user_has, user_is


def load_common_data():
    """
    私有方法，装载共用数据
    """

    return {
        'top_menu': 'service'
    }

@main.route('/blacklist')
@login_required
@user_has('admin_service')
def show_blacklist():
    top_orders = Order.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').limit(10).all()

    return render_template('service/show_blacklist.html',
                           top_orders=top_orders,
                           sub_menu='blacklist',
                           **load_common_data())


