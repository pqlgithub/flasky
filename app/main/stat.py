# -*- coding: utf-8 -*-
import time
import datetime
import pandas as pd
import numpy as np
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from ..decorators import user_has
from app.models import MasterStatistics, StoreStatistics, ProductStatistics, DaySkuStatistics, Store, Supplier
from ..utils import Master, full_response, R200_OK


@main.route('/stats')
@login_required
@user_has('admin_reports')
def stats():
    # 主账号当前月份统计
    month = time.strftime("%Y%m")
    master_statistics = MasterStatistics.query.filter_by(time=month, master_uid=Master.master_uid(), type=1).first()

    # 各店铺当前月份统计
    store_statistics = StoreStatistics.query.filter_by(time=month, master_uid=Master.master_uid(), type=1)\
        .order_by(StoreStatistics.store_id.asc()).all()

    return render_template('stats/index.html',
                           master_statistics=master_statistics,
                           store_statistics=store_statistics,
                           sub_menu='stats')


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
    ).order_by(ProductStatistics.income.desc()).all()

    data = []
    for v in product_top:
        data.append({
            'sku_serial_no': v.sku_serial_no,
            'income': v.income,
        })

    return full_response(True, R200_OK, data)


@main.route('/sales/statistics', methods=['GET'])
@login_required
@user_has('admin_reports')
def sales_statistic():
    """销售统计展示页面"""
    return render_template('stats/sales.html', sub_menu='sales')


@main.route('/sales/master', methods=['GET'])
@login_required
@user_has('admin_reports')
def sales_master():
    """主账户销售统计"""
    new_start_date = request.args.get("start_time")
    new_end_date = request.args.get("end_time")
    start_time, end_time = list(summary_time_range(new_start_date, new_end_date))

    day_sku_statistics = db.session.query(
        DaySkuStatistics.income, DaySkuStatistics.time).filter(
            DaySkuStatistics.time >= start_time).filter(
                DaySkuStatistics.time <= end_time).filter_by(
                    master_uid=Master.master_uid()).group_by('time')

    data = pd.read_sql(day_sku_statistics.statement, db.session.bind)

    # 时间开头和结尾空数据
    head_data = pd.DataFrame(
        [[0, start_time], [0, end_time]], columns=['income', 'time'])
    data = pd.concat([data, head_data])

    data['time'] = data['time'].apply(
        lambda x: datetime.datetime.fromtimestamp(x))

    data = data.set_index(data['time'])
    # print(data)
    data = data.resample('D', how="sum")
    # print(data)
    data = data.reset_index()
    data['time'] = data['time'].apply(lambda x: x.strftime("%Y-%m-%d"))

    data = data.fillna(0).to_dict(orient='list')

    return full_response(True, R200_OK, data)


@main.route('/sales/store', methods=['GET'])
@login_required
@user_has('admin_reports')
def sales_store():
    new_start_date = request.args.get("start_time")

    new_end_date = request.args.get("end_time")
    start_time, end_time = list(
        summary_time_range(new_start_date, new_end_date))

    day_sku_statistics = db.session.query(
        DaySkuStatistics.income,
        DaySkuStatistics.time, DaySkuStatistics.store_id).filter(
            DaySkuStatistics.time >= start_time).filter(
                DaySkuStatistics.time <= end_time).filter_by(
                    master_uid=Master.master_uid())
    data = pd.read_sql(day_sku_statistics.statement, db.session.bind)
    if not data.empty:
        data = data.groupby(['store_id', 'time']).sum().reset_index('time')

    stores = db.session.query(
        Store.id, Store.name).filter_by(master_uid=Master.master_uid()).all()

    refund_data = {}
    head_data = pd.DataFrame(
        [[0, start_time], [0, end_time]], columns=['income', 'time'])
    for store in stores:
        if store.id in data.index:
            new_data = pd.concat(
                [data.loc[store.id:store.id, :], head_data], axis=0)
        else:
            new_data = head_data.copy()

        new_data['time'] = new_data['time'].apply(
            lambda x: datetime.datetime.fromtimestamp(x))
        new_data = new_data.set_index(new_data['time']).resample(
            'D', how="sum").reset_index()
        new_data['time'] = new_data['time'].apply(
            lambda x: x.strftime("%Y-%m-%d"))

        refund_data[store.name] = new_data.fillna(0).to_dict('list')

    return full_response(True, R200_OK, refund_data)


@main.route('/sales/supplier', methods=['GET'])
@login_required
@user_has('admin_reports')
def sales_supplier():
    new_start_date = request.args.get("start_time")

    new_end_date = request.args.get("end_time")
    start_time, end_time = list(
        summary_time_range(new_start_date, new_end_date))
    
    day_sku_statistics = db.session.query(
        DaySkuStatistics.income,
        DaySkuStatistics.time, DaySkuStatistics.supplier_id).filter(
            DaySkuStatistics.time >= start_time).filter(
                DaySkuStatistics.time <= end_time).filter_by(
                    master_uid=Master.master_uid())
    data = pd.read_sql(day_sku_statistics.statement, db.session.bind)
    if not data.empty:
        data = data.groupby(['supplier_id', 'time']).sum().reset_index('time')

    suppliers = db.session.query(
        Supplier.id, Supplier.short_name).filter_by(master_uid=Master.master_uid()).all()

    refund_data = {}
    head_data = pd.DataFrame(
        [[0, start_time], [0, end_time]], columns=['income', 'time'])
    for supplier in suppliers:
        if supplier.id in data.index:
            new_data = pd.concat(
                [data.loc[supplier.id:supplier.id, :], head_data], axis=0)
        else:
            new_data = head_data.copy()

        new_data['time'] = new_data['time'].apply(
            lambda x: datetime.datetime.fromtimestamp(x))
        new_data = new_data.set_index(new_data['time']).resample(
            'D', how="sum").reset_index()
        new_data['time'] = new_data['time'].apply(
            lambda x: x.strftime("%Y-%m-%d"))
        refund_data[supplier.short_name] = new_data.fillna(0).to_dict('list')

    return full_response(True, R200_OK, refund_data)


def summary_time_range(start_time, end_time):
    """ 时间字符串转时间戳 """
    today = datetime.date.today()
    # 默认结束时间
    default_end_date = datetime.datetime.combine(today, datetime.time())
    # 默认开始时间
    default_start_date = default_end_date - datetime.timedelta(days=6)

    if start_time != '' and end_time != '' and start_time is not None and end_time is not None:
        default_start_date = datetime.datetime.strptime(start_time, "%Y-%m-%d")
        default_end_date = datetime.datetime.strptime(end_time, "%Y-%m-%d")

    start_time = int(default_start_date.timestamp())
    end_time = int(default_end_date.timestamp())

    return start_time, end_time
