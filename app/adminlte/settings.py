# -*- coding: utf-8 -*-
from flask import redirect, url_for, current_app, render_template, flash
from . import adminlte
from .. import db, cache
from app.models import WxToken, WxAuthCode
from app.helpers import WxApp, WxAppError
from app.utils import custom_response, timestamp


@adminlte.route('/settings')
def setting_index():
    return render_template('adminlte/settings/index.html')


