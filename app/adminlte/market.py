# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_babelex import gettext
from . import adminlte
from .. import db
from app.models import Client
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, R400_BADREQUEST, Master, custom_response



@adminlte.route('/market')
def show_market(page=1):
    """服务市场服务列表"""
    pass
