# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from ..decorators import user_has
from app.models import MasterStatistics, StoreStatistics, ProductStatistics
from ..utils import Master, full_response, R200_OK
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
        time=month, master_uid=Master.master_uid(),
        type=1).order_by("store_id").all()

    return render_template(
        'stats/index.html',
        master_statistics=master_statistics,
        store_statistics=store_statistics,
    )


@main.route('/stats/store_sku_top', methods=['POST'])
@login_required
@user_has('admin_reports')
def store_sku_top():
    """获取店铺sku销售排行"""
    store_id = request.form.get('store_id', type=int)

    month = datetime.datetime.now().strftime("%Y%m")
    product_top = ProductStatistics.query.filter_by(
        store_id=store_id,
        type=2,
        time_type=1,
        time=month,
    ).order_by('income desc').all()

    data = []
    for v in product_top:
        data.append({
            'sku_serial_no': v.sku_serial_no,
            'income': v.income,
        })

    return full_response(True,R200_OK,data)


