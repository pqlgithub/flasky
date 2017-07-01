# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from ..decorators import user_has, user_is
from ..utils import gen_serial_no
from app.models import Product, Order


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'logistics'
    }

@main.route('/logistics')
@main.route('/logistics/<int:page>')
#@user_has('view_orders')
def show_expresses(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_express = Order.query.order_by('created_at desc').paginate(page, per_page)

    return render_template('logistics/show_list.html',
                           sub_menu='express',
                           paginated_express=paginated_express, **load_common_data())


@main.route('/expresses/create', methods=['GET', 'POST'])
def create_express():
    pass


@main.route('/expresses/delete', methods=['POST'])
def delete_express():
    pass