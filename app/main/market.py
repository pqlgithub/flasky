# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_sqlalchemy import Pagination
from . import main
from .. import db
from ..utils import Master, status_response, timestamp, custom_response
from ..decorators import user_has
from ..constant import SERVICE_TYPES
from app.models import AppService, SubscribeService, Coupon
from app.forms import CouponForm
from app.helpers import MixGenId, WxPay, WxPayError


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'market'
    }


@main.route('/market/apps')
def show_apps():

    # 获取已发布应用
    market_apps = AppService.query.filter_by(type=1, status=2).order_by(AppService.created_at.asc()).all()
    channel_apps = AppService.query.filter_by(type=2, status=2).order_by(AppService.created_at.asc()).all()
    supply_apps = AppService.query.filter_by(type=3, status=2).order_by(AppService.created_at.asc()).all()
    
    return render_template('app_store/show_list.html',
                           sub_menu='app_store',
                           app_types=SERVICE_TYPES,
                           market_apps=market_apps,
                           channel_apps=channel_apps,
                           supply_apps=supply_apps,
                           **load_common_data())


@main.route('/market/apps/subscribed')
@user_has('admin_app_store')
def subscribed_apps():
    """已订购应用列表"""
    subscribe_services = SubscribeService.query.filter_by(master_uid=Master.master_uid()).all()

    app_services = []
    for subscribe in subscribe_services:
        app_service = AppService.query.get(subscribe.service_id)
        if app_service:
            app_service_info = app_service.to_json()
            app_service_info['is_paid'] = subscribe.is_paid
            app_service_info['expired_at'] = subscribe.expired_at

            app_services.append(app_service_info)

    return render_template('app_store/subscribed_list.html',
                           sub_menu='subscribed',
                           subscribe_services=subscribe_services,
                           app_services=app_services,
                           **load_common_data())


@main.route('/market/apps/show')
def view_app_detail():
    """查看某应用"""
    rid = request.args.get('rid')
    app_service = AppService.query.filter_by(serial_no=rid, status=2).first()
    if app_service is None:
        abort(404)

    return render_template('app_store/view_detail.html',
                           app_service=app_service,
                           sub_menu='app_store',
                           **load_common_data())


@main.route('/market/apps/submit_subscribe')
def submit_subscribe():
    """确认订购信息"""
    rid = request.args.get('rid')
    app_service = AppService.query.filter_by(serial_no=rid, status=2).first()
    if app_service is None:
        abort(404)

    # 验证是否存在有效（未过期）的记录
    subscribe_service = SubscribeService.query.filter_by(master_uid=Master.master_uid(),
                                                         service_id=app_service.id, status=1).first()

    pay_params = {}
    # 未购买过
    if not subscribe_service:

        # 免费的
        if app_service.is_free:
            try:
                subscribe_service = SubscribeService(
                    master_uid=Master.master_uid(),
                    service_id=app_service.id,
                    service_serial_no=app_service.serial_no,
                    trade_no=MixGenId.gen_trade_no(),
                    trade_content=app_service.title,
                    pay_amount=0.00,
                    total_amount=0.00,
                    pay_mode=1,
                    is_paid=True,
                    discount_amount=0.00,
                    ordered_at=int(timestamp()),
                    ordered_days=1,
                    status=1
                )
                db.session.add(subscribe_service)

                db.session.commit()
            except Exception as err:
                current_app.logger.warn('Subscribe service fail: %s' % str(err))
                db.session.rollback()
                flash('订购此应用失败，请重试！', 'danger')
                return redirect('%s?rid=%s' % (url_for('.view_app_detail'), rid))

            # 直接跳转至已订购列表
            return redirect(url_for('.subscribed_apps'))

        else:  # 收费的
            subscribe_service = SubscribeService(
                master_uid=Master.master_uid(),
                service_id=app_service.id,
                service_serial_no=app_service.serial_no,
                trade_no=MixGenId.gen_trade_no(),
                trade_content=app_service.title,
                pay_amount=app_service.sale_price,
                total_amount=app_service.sale_price,
                pay_mode=1,  # 默认：1， 微信支付
                is_paid=False,
                discount_amount=0.00,
                ordered_at=int(timestamp()),
                ordered_days=365,
                status=1
            )
            db.session.add(subscribe_service)

            db.session.commit()

            # 跳转至待支付页面
            pay_params = _js_wxpay_params(rid=subscribe_service.trade_no, subscribe_service=subscribe_service)

            return render_template('app_store/submit_subscribe.html',
                                   subscribe_service=subscribe_service,
                                   app_service=app_service,
                                   pay_params=pay_params,
                                   sub_menu='app_store',
                                   **load_common_data())

    else:  # 已订购过此服务
        # 收费的
        # 验证是否支付，订单保留48小时，然后将删除未支付订单
        if not subscribe_service.is_paid:
            # 跳转去支付
            pay_params = _js_wxpay_params(rid=subscribe_service.trade_no, subscribe_service=subscribe_service)
            return render_template('app_store/submit_subscribe.html',
                                   subscribe_service=subscribe_service,
                                   app_service=app_service,
                                   pay_params=pay_params,
                                   sub_menu='app_store',
                                   **load_common_data())

    # 支付后，直接跳转
    return redirect(url_for('.subscribed_apps'))


@main.route('/market/apps/subscribe_payment', methods=['POST'])
def subscribe_payment():
    """订购支付"""
    rid = request.form.get('rid')
    pay_mode = request.form.get('pay_mode', 1, type=int)
    coupon_code = request.form.get('coupon_code')
    discount_amount = request.form.get('discount_amount')

    subscribe_service = SubscribeService.query.filter_by(master_uid=Master.master_uid(),
                                                         trade_no=rid).first()
    if subscribe_service is None:
        return custom_response(False, '此订购单号不存在')

    # 微信支付
    if pay_mode == 1:
        return _js_wxpay_params(rid=rid, subscribe_service=subscribe_service)


def _js_wxpay_params(rid, subscribe_service):
    """获取支付参数"""
    cfg = current_app.config

    notify_url = '%s/%s' % (cfg['DOMAIN_URL'], url_for('open.wxpay_service_notice'))
    wxpay = WxPay(
        wx_app_id=cfg['WXPAY_APP_ID'],
        wx_mch_id=cfg['WXPAY_MCH_ID'],
        wx_mch_key=cfg['WXPAY_MCH_SECRET'],
        wx_notify_url=notify_url)
    pay_params = {}

    try:
        prepay_result = wxpay.unified_order(
            body=subscribe_service.trade_content,
            out_trade_no=rid,
            product_id=subscribe_service.service_serial_no,
            total_fee=str(int(subscribe_service.pay_amount * 100)),  # total_fee 单位是 分， 100 = 1元
            trade_type='NATIVE')

        current_app.logger.warn('Subscribe order result: %s' % prepay_result)

        if prepay_result and prepay_result['prepay_id']:
            prepay_id = prepay_result['prepay_id']

            # 生成签名
            pay_params = {
                'appId': cfg['WXPAY_APP_ID'],
                'nonceStr': WxPay.nonce_str(32),
                'package': 'prepay_id=%s' % prepay_id,
                'signType': 'MD5',
                'timeStamp': int(timestamp())
            }
            pay_sign = wxpay.sign(pay_params)

            pay_params['pay_sign'] = pay_sign
            pay_params['prepay_id'] = prepay_id
            pay_params['code_url'] = prepay_result['code_url']
    except WxPayError as err:
        current_app.logger.warn('订购订单支付失败：%s' % str(err))

    return pay_params


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
                           pagination=pagination,
                           sub_menu='coupon',
                           **load_common_data())


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
                           pagination=paginated_coupons,
                           sub_menu='coupon',
                           **load_common_data())


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
                           form=form,
                           sub_menu='coupon',
                           **load_common_data())


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
