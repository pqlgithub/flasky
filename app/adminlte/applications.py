# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request
from flask_babelex import gettext
from . import adminlte
from .. import db
from app.models import AppService
from app.forms import ApplicationForm
from ..utils import custom_response
from ..constant import SERVICE_TYPES

def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'markets',
        'service_types': SERVICE_TYPES
    }

@adminlte.route('/applications')
def show_applications(page=1):
    """服务市场服务列表"""
    per_page = request.args.get('per_page', 10, type=int)
    type = request.args.get('t', 0, type=int)

    if not type:
        query = AppService.query
    else:
        query = AppService.query.filter_by(type=type)

    paginated_markets = query.order_by(AppService.created_at.desc()).paginate(page, per_page)

    return render_template('adminlte/applications/show_list.html',
                           paginated_markets=paginated_markets,
                           t=type,
                           **load_common_data())


@adminlte.route('/applications/create', methods=['GET', 'POST'])
def create_application():
    """创建官方应用服务"""
    form = ApplicationForm()
    if form.validate_on_submit():
        app_service =  AppService(
            name=form.name.data,
            icon_id=form.icon_id.data,
            summary=form.summary.data,
            type=form.type.data,
            is_free=form.is_free.data,
            # 收费价格
            sale_price=form.sale_price.data,
            description=form.description.data,
            remark=form.remark.data,
            status=form.status.data
        )
        db.session.add(app_service)
        db.session.commit()
        
        flash(gettext('Add Application is ok!'), 'success')
        
        return redirect(url_for('.show_applications'))
    
    mode = 'create'
    return render_template('adminlte/applications/create_and_edit.html',
                           form=form,
                           mode=mode,
                           **load_common_data())

@adminlte.route('/applications/<string:sn>/edit', methods=['GET', 'POST'])
def edit_application(sn):
    """更新应用服务信息"""
    app_service = AppService.query.filter_by(serial_no=sn).first()
    if app_service is None:
        abort(404)
        
    form = ApplicationForm()
    if form.validate_on_submit():
        form.populate_obj(app_service)
        
        db.session.commit()

        flash(gettext('Update Application is ok!'), 'success')

        return redirect(url_for('.show_applications'))
        
    mode = 'edit'
    form.name.data = app_service.name
    form.icon_id.data = app_service.icon_id
    form.summary.data = app_service.summary
    form.type.data = app_service.type
    form.is_free.data = app_service.is_free
    form.sale_price.data = app_service.sale_price
    form.description.data = app_service.description
    form.remark.data = app_service.remark
    form.status.data = app_service.status
    
    return render_template('adminlte/applications/create_and_edit.html',
                           form=form,
                           mode=mode,
                           **load_common_data())


@adminlte.route('/applications/<string:sn>/published', methods=['POST'])
def published_application(sn):
    """上架应用服务"""
    app_service = AppService.query.filter_by(serial_no=sn).first()
    if app_service is None:
        abort(404)
    
    app_service.mark_set_published()
    
    db.session.commit()

    return custom_response(True, gettext('Application has already published!'))
    

@adminlte.route('/applications/disabled', methods=['POST'])
def disabled_application():
    """禁用应用服务"""
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Disabled application is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            app_service = AppService.query.get_or_404(int(id))
            app_service.mark_set_disabled()
        
        db.session.commit()
    
        flash('Disabled service is ok!', 'success')
    except:
        db.session.rollback()
        flash('Disabled service is fail!', 'danger')
        
    return redirect(url_for('.show_applications'))