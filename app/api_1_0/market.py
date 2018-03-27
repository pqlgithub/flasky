# -*- coding: utf-8 -*-
import json
import hashlib
from decimal import Decimal
from flask import request, abort, url_for, g, current_app
from sqlalchemy.exc import IntegrityError

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Coupon, UserCoupon, WxAuthorizer, Asset, Product, WxMiniApp
from app.helpers import WxaOpen3rd, WxAppError, Fxaim
from app.utils import datestr_to_timestamp, timestamp
from qiniu import Auth, put_data, etag, urlsafe_base64_encode


@api.route('/market/wxacode', methods=['POST'])
def get_wxacode_card():
    """获取推广商品的小程序码"""
    auth_app_id = request.json.get('auth_app_id')
    path = request.json.get('path')
    rid = request.json.get('rid')

    current_app.logger.warn('path: %s, rid: %s' % (path, rid))

    # 商品是否存在
    product = Product.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()

    # 小程序名称
    wxa = WxMiniApp.query.filter_by(master_uid=g.master_uid, auth_app_id=auth_app_id).first_or_404()

    try:
        # 获取授权信息
        authorizer = WxAuthorizer.query.filter_by(master_uid=g.master_uid, auth_app_id=auth_app_id).first_or_404()
        # 获得小程序码
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.get_wxacode_unlimit(path, scene=rid)
    except WxAppError as err:
        current_app.logger.warn('Wxapp wxacode is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': str(err)
        })

    # 构建鉴权对象
    cfg = current_app.config
    q = Auth(cfg['QINIU_ACCESS_KEY'], cfg['QINIU_ACCESS_SECRET'])

    # 上传到七牛后保存的文件名
    key = 'qrcode/wxacode-%s-%s.jpg' % (rid, hashlib.md5(path.encode(encoding='UTF-8')).hexdigest())
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(cfg['QINIU_BUCKET_NAME'], key, 3600)
    # 开始上传
    ret, info = put_data(token, key, result.content)

    current_app.logger.warn('ret: %s' % ret)
    current_app.logger.warn('info: %s' % info)

    # 生成小程序码
    wxa_image_url = '%s/%s' % (Asset.host_url(), key)

    if product.sale_price > 0:
        sale_price = product.sale_price
    else:
        sale_price = product.price

    data = {
        'title': product.name,
        'sale_price': str(sale_price.quantize(Decimal('0.00'))),
        'goods_img': product.cover.view_url,
        'brand_name': wxa.nick_name,
        'logo_img': wxa.head_img,
        'qr_code_img': wxa_image_url
    }

    # 发起请求
    fxaim = Fxaim()
    result = fxaim.get_wxa_poster(data)

    return full_response(R200_OK, {
        'wxa_image': result.image_url
    })


@api.route('/market/banners')
def get_banners():
    """获取广告列表"""
    pass


@api.route('/market/banners/create', methods=['POST'])
def create_banner():
    """新增广告图"""
    pass


@api.route('/market/banners/update', methods=['PUT'])
def update_banner():
    """更新广告图"""
    pass


@api.route('/market/banners/delete', methods=['DELETE'])
def delete_banner():
    """删除广告图"""
    pass


@api.route('/market/coupons')
def get_coupons():
    """平台-获取优惠券列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    used = request.values.get('used')
    status = request.values.get('status', 1)
    
    builder = Coupon.query.filter_by(master_uid=g.master_uid, status=status)

    pagination = builder.paginate(page, per_page=per_page, error_out=False)
    coupon_list = pagination.items
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_bonus_list', page=page - 1, _external=True)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_bonus_list', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'coupons': [coupon.to_json() for coupon in coupon_list],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/market/coupons/activity', methods=['POST'])
@auth.login_required
def get_activity_coupons():
    """平台-获取当前活动的优惠券"""
    coupons = Coupon.query.filter_by(master_uid=g.master_uid, status=1).order_by(Coupon.end_date.asc()).all()

    # 检测当前用户是否已领取
    coupon_ids = [coupon.id for coupon in coupons]
    user_coupons = UserCoupon.query.filter_by(user_id=g.current_user.id).filter(UserCoupon.coupon_id.in_(coupon_ids)).all()
    if not user_coupons:
        activity_coupons = [coupon.to_json() for coupon in coupons]
    else:
        grant_ids = [user_coupon.coupon_id for user_coupon in user_coupons]
        activity_coupons = [coupon.to_json() for coupon in coupons if coupon.id not in grant_ids]

    return full_response(R200_OK, {
        'activity_coupons': activity_coupons
    })


@api.route('/market/coupons/<string:rid>/disabled', methods=['POST'])
@auth.login_required
def disabled_coupon(rid):
    """平台-禁用红包"""
    coupon = Coupon.query.filter_by(master_uid=g.master_uid, code=rid).first()
    if coupon is None:
        abort(404)

    coupon.mark_set_disabled()

    db.session.commit()

    return status_response(R200_OK)


@api.route('/market/coupons/create', methods=['POST'])
@auth.login_required
def create_coupons():
    """平台-添加新优惠券"""
    if not request.json or 'amount' not in request.json:
        abort(400)

    # todo: 验证用户身份，必须主账号权限用户

    # todo: 数据验证

    try:
        coupon = Coupon(
            master_uid=g.master_uid,
            name=request.json.get('name'),
            amount=request.json.get('amount'),
            type=request.json.get('type'),
            start_date=request.json.get('start_date'),
            end_date=request.json.get('end_date'),
            min_amount=request.json.get('min_amount'),
            reach_amount=request.json.get('reach_amount'),
            product_rid=request.json.get('product_rid'),
            status=request.json.get('status')
        )
        db.session.add(coupon)
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Create coupon fail: {}'.format(str(err)))

        db.session.rollback()
        return status_response(custom_status('Create failed!', 400), False)

    return full_response(R201_CREATED, coupon.to_json())


@api.route('/market/coupons/<string:rid>')
def get_coupon(rid):
    """用户-获取优惠券信息"""
    coupon = Coupon.query.filter_by(master_uid=g.master_uid, code=rid).first()
    if coupon is None:
        return status_response(R404_NOTFOUND, False)

    return full_response(R200_OK, coupon.to_json())


@api.route('/market/user_coupons', methods=['POST'])
@auth.login_required
def get_user_coupons():
    """用户-获取红包列表"""
    page = request.json.get('page')
    per_page = request.json.get('per_page')
    status = request.json.get('status')

    builder = UserCoupon.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id)
    if status == 'N01':  # 未使用
        builder = builder.filter_by(is_used=False)
    elif status == 'N03':  # 已过期
        builder = builder.join(Coupon, Coupon.id == UserCoupon.coupon_id).filter(Coupon.end_date < int(timestamp()))
    else:  # 已使用
        builder = builder.filter_by(is_used=True)

    pagination = builder.paginate(page, per_page=per_page, error_out=False)
    coupons = pagination.items
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_user_bonus', page=page - 1, _external=True)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_user_bonus', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'coupons': [coupon.to_json() for coupon in coupons],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/market/coupons/available', methods=['POST'])
@auth.login_required
def get_available_coupons():
    """用户-获取符合条件的红包列表"""
    total_amount = request.json.get('pay_amount')

    if not total_amount:
        abort(400)

    user_coupons = UserCoupon.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id, is_used=False).all()
    available_coupons = []
    total_amount = Decimal(total_amount)
    if user_coupons:
        # 过滤是否满足条件
        for user_coupon in user_coupons:
            coupon = user_coupon.coupon
            if coupon.type == 3 and coupon.reach_amount < total_amount:
                available_coupons.append(coupon.to_json())
            elif coupon.type == 2 and coupon.min_amount < total_amount:
                available_coupons.append(coupon.to_json())
            else:
                available_coupons.append(coupon.to_json())

        # 自动匹配优惠最大金额
        if len(available_coupons):
            coupon_amount = [ac['amount'] for ac in available_coupons]
            max_index = coupon_amount.index(max(coupon_amount))
            available_coupons[max_index]['max'] = True

    return full_response(R200_OK, {
        'available_coupons': available_coupons
    })


@api.route('/market/coupons/grant', methods=['POST'])
@auth.login_required
def grant_coupons():
    """用户-领取优惠券"""
    if not request.json or 'rid' not in request.json:
        abort(400)
    rid = request.json.get('rid')
    coupon = Coupon.query.filter_by(master_uid=g.master_uid, code=rid).first()
    if coupon is None:
        return status_response(R404_NOTFOUND, False)

    user_coupon = UserCoupon.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id,
                                             coupon_id=coupon.id).first()
    if user_coupon is None:
        # 新增
        user_coupon = UserCoupon(
            master_uid=g.master_uid,
            user_id=g.current_user.id,
            coupon_id=coupon.id,
            get_at=int(timestamp())
        )
        db.session.add(user_coupon)

        # 同步更新优惠券领取总数
        coupon.got_count += 1

        db.session.commit()

    return status_response(R201_CREATED)
