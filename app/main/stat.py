# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from ..decorators import user_has
from app.models import MasterStatistics, StoreStatistics
from ..utils import Master
import time
import datetime


@main.route('/stats')
@login_required
@user_has('admin_reports')
def stats():
    # 主账号当前月份统计
    month = time.strftime("%Y%m")
    master_statistics = MasterStatistics.query.filter_by(
        time=month, master_uid=Master.master_uid(), type=1).first()


    # 各店铺当前月份统计
    store_statistics = StoreStatistics.query.filter_by(
        time=month, master_uid=Master.master_uid(), type=1).order_by("store_id").all()
    
        
    return render_template('stats/index.html',
                           master_statistics=master_statistics,
                           store_statistics=store_statistics,)
