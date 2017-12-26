# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from . import main
from .. import db
from ..utils import Master
from ..decorators import user_has
from ..constant import SERVICE_TYPES
from app.models import AppService, SubscribeService, SubscribeRecord


@main.route('/app_store')
@main.route('/app_store/<int:page>')
@login_required
@user_has('admin_app_store')
def show_apps(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    # 获取已上架应用
    builder = AppService.query.filter_by(status=2)
    # 排序
    paginated_apps = builder.order_by(AppService.created_at.desc()).all()
    
    return render_template('app_store/show_list.html',
                           sub_menu='app_store',
                           app_types=SERVICE_TYPES,
                           paginated_apps=paginated_apps)


@main.route('/app_store/<string:sn>/subscribe', methods=['GET', 'POST'])
def subscribe_app(sn):
    """订购某应用"""
    app_service = AppService.query.filter_by(serial_no=sn).first()
    if app_service is None:
        abort(404)
        
    subscribe_service = SubscribeService(
        master_uid=Master.master_uid(),
        service_id=app_service.id,
        status=-1
    )
    db.session.add(subscribe_service)
    db.session.commit()
    
    flash('Subscribe service is ok!', 'success')
    
    return redirect(url_for('.show_apps'))
    
    