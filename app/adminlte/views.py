# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_babelex import gettext
from . import adminlte
from .. import db
from app.models import User, Role, Ability, Site
from app.forms import RoleForm, AbilityForm, SiteForm, UserForm, PasswdForm
import app.constant as constant
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, R400_BADREQUEST, Master, custom_response


@adminlte.before_request
@login_required
def before_request():
    pass


@adminlte.route('/')
def admin_index():
    """管理首页"""
    return render_template('adminlte/index.html')