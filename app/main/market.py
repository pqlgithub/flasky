# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_sqlalchemy import Pagination
from . import main
from .. import db
from ..utils import Master, datestr_to_timestamp, status_response
from ..decorators import user_has
from ..constant import SERVICE_TYPES
from app.models import AppService, SubscribeService, SubscribeRecord, Bonus
from app.forms import BonusForm


@main.route('/market/apps')
@main.route('/market/apps/<int:page>')
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


@main.route('/market/apps/<string:sn>/subscribe', methods=['GET', 'POST'])
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


@main.route('/market/bonus/search', methods=['GET', 'POST'])
def search_bonus():
    """搜索红包"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    used_id = request.values.get('used_id', type=int)
    sk = request.values.get('sk', type=str, default='ad')

    builder = Bonus.query.filter_by(master_uid=Master.master_uid())

    if used_id == 1:
        builder = builder.filter_by(is_used=True)
    elif used_id == -1:
        builder = builder.filter_by(is_used=False)

    qk = qk.strip()
    if qk:
        builder = builder.filter_by(code=qk)

    bonus = builder.order_by(Bonus.created_at.desc()).all()

    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))

    paginated_bonus = bonus[start:end]

    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    return render_template('bonus/search_result.html',
                           qk=qk,
                           sk=sk,
                           used_id=used_id,
                           paginated_bonus=paginated_bonus,
                           pagination=pagination)


@main.route('/market/bonus')
def show_bonus():
    """红包管理"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    builder = Bonus.query.filter_by(master_uid=Master.master_uid())
    # 排序
    paginated_bonus = builder.order_by(Bonus.created_at.asc()).paginate(page, per_page)

    return render_template('bonus/show_list.html',
                           paginated_bonus=paginated_bonus.items,
                           pagination=paginated_bonus
                           )


@main.route('/market/bonus/create', methods=['GET', 'POST'])
def create_bonus():
    """新增红包"""
    form = BonusForm()
    if form.validate_on_submit():
        quantity = form.quantity.data

        expired_at = 0
        if form.expired_at.data:
            expired_at = datestr_to_timestamp(form.expired_at.data)

        for idx in range(quantity):
            bonus = Bonus(
                master_uid=Master.master_uid(),
                amount=form.amount.data,
                expired_at=expired_at,
                min_amount=form.min_amount.data,
                xname=form.xname.data,
                product_rid=form.product_rid.data,
                status=form.status.data
            )
            db.session.add(bonus)

        db.session.commit()

        flash('新增红包成功！', 'success')
        return redirect(url_for('main.show_bonus'))
    else:
        current_app.logger.warn(form.errors)

    mode = 'create'
    return render_template('bonus/create_and_edit.html',
                           mode=mode,
                           form=form)


@main.route('/market/bonus/<string:rid>/disabled', methods=['POST'])
def disabled_bonus(rid):
    """使红包作废"""
    bonus = Bonus.query.filter_by(master_uid=Master.master_uid(), code=rid).first_or_404()
    bonus.mark_set_disabled()
    db.session.commit()

    return status_response()


@main.route('/market/bonus/delete', methods=['POST'])
def delete_bonus():
    """删除红包"""
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete bonus is null!', 'danger')
        abort(404)

    for rid in selected_ids:
        bonus = Bonus.query.filter_by(master_uid=Master.master_uid(), code=rid).first()
        if bonus.master_uid != Master.master_uid():
            abort(401)
        db.session.delete(bonus)
    db.session.commit()

    flash('Delete bonus is ok!', 'success')

    return redirect(url_for('.show_bonus'))




