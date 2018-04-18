# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_sqlalchemy import Pagination
from . import main
from .. import db
from ..utils import Master, status_response
from ..decorators import user_has
from ..constant import SERVICE_TYPES
from app.models import AppService, SubscribeService, Coupon
from app.forms import CouponForm


@main.route('/market/apps')
@main.route('/market/apps/<int:page>')
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


@main.route('/market/coupons/search', methods=['GET', 'POST'])
def search_coupons():
    """搜索优惠券"""
    per_page = request.values.get('per_page', 25, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    sk = request.values.get('sk', type=str, default='ad')

    builder = Coupon.query.filter_by(master_uid=Master.master_uid())

    qk = qk.strip()
    if qk:
        builder = builder.filter_by(code=qk)

    coupons = builder.order_by(Coupon.created_at.desc()).all()

    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))

    paginated_coupons = coupons[start:end]

    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    return render_template('bonus/search_result.html',
                           qk=qk,
                           sk=sk,
                           paginated_coupons=paginated_coupons,
                           pagination=pagination)


@main.route('/market/coupons')
def show_coupons():
    """优惠券管理"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    builder = Coupon.query.filter_by(master_uid=Master.master_uid())
    # 排序
    paginated_coupons = builder.order_by(Coupon.created_at.desc()).paginate(page, per_page)

    return render_template('coupon/show_list.html',
                           paginated_coupons=paginated_coupons.items,
                           pagination=paginated_coupons
                           )


@main.route('/market/coupons/create', methods=['GET', 'POST'])
def create_coupon():
    """新增红包"""
    form = CouponForm()
    if form.validate_on_submit():
        coupon = Coupon(
            master_uid=Master.master_uid(),
            name=form.name.data,
            amount=form.amount.data,
            type=form.type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            min_amount=form.min_amount.data,
            reach_amount=form.reach_amount.data,
            product_rid=form.product_rid.data,
            status=form.status.data
        )
        db.session.add(coupon)

        db.session.commit()

        flash('新增优惠券成功！', 'success')
        return redirect(url_for('main.show_coupons'))
    else:
        current_app.logger.warn(form.errors)

    mode = 'create'
    return render_template('coupon/create_and_edit.html',
                           mode=mode,
                           form=form)


@main.route('/market/coupons/<string:rid>/disabled', methods=['POST'])
def disabled_coupon(rid):
    """使优惠券作废"""
    coupon = Coupon.query.filter_by(master_uid=Master.master_uid(), code=rid).first_or_404()
    coupon.mark_set_disabled()
    db.session.commit()

    return status_response()


@main.route('/market/coupons/delete', methods=['POST'])
def delete_coupon():
    """删除优惠券"""
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete coupon is null!', 'danger')
        abort(404)

    for rid in selected_ids:
        bonus = Coupon.query.filter_by(master_uid=Master.master_uid(), code=rid).first()
        if bonus.master_uid != Master.master_uid():
            abort(401)
        db.session.delete(bonus)
    db.session.commit()

    flash('Delete coupon is ok!', 'success')

    return redirect(url_for('.show_coupons'))
