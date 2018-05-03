# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_babelex import gettext
from . import adminlte
from .. import db
from app.models import AppService, UserEdition, EditionService
from app.forms import ApplicationForm
from ..utils import custom_response, flash_errors, correct_decimal
from ..constant import SERVICE_TYPES

# 系统版本
system_edition = [
    {
        'id': UserEdition.FREE,
        'title': '免费版'
    },
    {
        'id': UserEdition.PROFESSIONAL,
        'title': '专业版'
    },
    {
        'id': UserEdition.ENTERPRISE,
        'title': '企业版'
    }
]


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
    _type = request.args.get('t', 0, type=int)
    edition_id = request.args.get('edition_id', type=int)

    if edition_id:
        paginated_markets = EditionService.query.filter_by(edition_id=edition_id).paginate(page, per_page)

        apps = []
        for item in paginated_markets.items:
            apps.append(AppService.query.get(item.service_id))

        paginated_markets.items = apps
    else:
        builder = AppService.query

        if _type:
            builder = builder.filter_by(type=_type)

        paginated_markets = builder.order_by(AppService.created_at.desc()).paginate(page, per_page)

    return render_template('adminlte/applications/show_list.html',
                           paginated_markets=paginated_markets,
                           edition_id=edition_id,
                           t=_type,
                           **load_common_data())


@adminlte.route('/applications/create', methods=['GET', 'POST'])
def create_application():
    """创建官方应用服务"""
    form = ApplicationForm()

    if request.method == 'POST':
        if form.validate_on_submit():

            app_service = AppService(
                name=form.name.data,
                title=form.title.data,
                icon_id=form.icon_id.data,
                summary=form.summary.data,
                type=form.type.data,
                is_free=form.is_free.data,
                # 收费价格
                sale_price=correct_decimal(form.sale_price.data),
                description=form.description.data,
                remark=form.remark.data,
                status=form.status.data
            )
            db.session.add(app_service)

            # 验证是否选择版本套餐
            edition_ids = request.form.getlist('edition_id[]')
            if edition_ids:
                for edition_id in edition_ids:
                    edition_service = EditionService.query.filter_by(edition_id=edition_id, service_id=app_service.id).first()
                    if edition_service is None:
                        edition_service = EditionService(
                            edition_id=edition_id,
                            service_id=app_service.id
                        )
                        db.session.add(edition_service)

            db.session.commit()

            flash(gettext('Add Application is ok!'), 'success')

            return redirect(url_for('.show_applications'))
        else:
            flash_errors(form)
            current_app.logger.debug(form.errors)
    
    mode = 'create'
    return render_template('adminlte/applications/create_and_edit.html',
                           system_edition=system_edition,
                           checked_edition_ids=[],
                           form=form,
                           mode=mode,
                           **load_common_data())


@adminlte.route('/applications/<string:sn>/edit', methods=['GET', 'POST'])
def edit_application(sn):
    """更新应用服务信息"""
    app_service = AppService.query.filter_by(serial_no=sn).first()
    if app_service is None:
        abort(404)

    # 已选择的版本
    checked_editions = EditionService.query.filter_by(service_id=app_service.id).all()
    checked_edition_ids = [checked_edition.edition_id for checked_edition in checked_editions]

    form = ApplicationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(app_service)

            # 验证是否选择版本套餐
            edition_ids = request.form.getlist('edition_id[]')
            if edition_ids:
                for checked_edition in checked_editions:
                    if checked_edition.edition_id not in edition_ids:
                        db.session.delete(checked_edition)

                for edition_id in edition_ids:
                    edition_service = EditionService.query.filter_by(edition_id=edition_id,
                                                                     service_id=app_service.id).first()
                    if edition_service is None:
                        edition_service = EditionService(
                            edition_id=edition_id,
                            service_id=app_service.id
                        )
                        db.session.add(edition_service)

            db.session.commit()

            flash(gettext('Update Application is ok!'), 'success')

            return redirect(url_for('.show_applications'))
        else:
            flash_errors(form)
        
    mode = 'edit'

    form.name.data = app_service.name
    form.title.data = app_service.title
    form.icon_id.data = app_service.icon_id
    form.summary.data = app_service.summary
    form.type.data = app_service.type
    form.is_free.data = app_service.is_free
    form.sale_price.data = app_service.sale_price
    form.description.data = app_service.description
    form.remark.data = app_service.remark
    form.status.data = app_service.status
    
    return render_template('adminlte/applications/create_and_edit.html',
                           checked_edition_ids=checked_edition_ids,
                           system_edition=system_edition,
                           app_service=app_service,
                           form=form,
                           mode=mode,
                           **load_common_data())


@adminlte.route('/applications/<string:sn>/published', methods=['POST'])
def published_application(sn):
    """上架应用服务"""
    status = request.values.get('status', type=int)

    app_service = AppService.query.filter_by(serial_no=sn).first()
    if app_service is None:
        abort(404)

    if status == 2:
        app_service.mark_set_published()

    if status == 1:
        app_service.mark_set_pending()
    
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
