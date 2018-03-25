# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for, current_app
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.helpers import WxPay, WxPayError
from app.models import Order, OrderItem, Address, ProductSku, Warehouse, OrderStatus
from app.utils import timestamp
from app.tasks import remove_order_cart, update_coupon_status, sync_product_stock


@api.route('/orders')
@auth.login_required
def get_orders():
    """订单列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    status = request.values.get('status', type=int)
    prev_url = None
    next_url = None

    builder = Order.query.filter_by(master_uid=g.master_uid, user_id=g.current_user.id)
    
    if status:
        builder = builder.filter_by(status=status)
    
    pagination = builder.order_by(Order.created_at.desc()).paginate(page, per_page, error_out=False)

    orders = pagination.items
    if pagination.has_prev:
        prev_url = url_for('api.get_orders', status=status, page=page - 1, _external=True)

    if pagination.has_next:
        next_url = url_for('api.get_orders', status=status, page=page + 1, _external=True)
    
    return full_response(R200_OK, {
        'orders': [order.to_json() for order in orders],
        'prev': prev_url,
        'next': next_url,
        'count': pagination.total
    })


@api.route('/orders/<string:rid>')
@auth.login_required
def get_order(rid):
    """订单详情"""
    order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    if not is_owner(order.user_id):
        abort(401)
    
    return full_response(R200_OK, order.to_json())


@api.route('/orders/freight')
@auth.login_required
def get_freight():
    """获取邮费"""
    freight = 0
    
    return full_response(R200_OK, {
        'freight': freight
    })


@api.route('/orders/<string:rid>/seller_remark', methods=['PUT'])
@auth.login_required
def add_seller_remark(rid):
    """添加卖家备注"""
    remark = request.json.get('remark')
    order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    if not can_admin(order.master_uid):
        abort(401)

    order.remark = remark

    db.session.commit()
    
    return status_response(R200_OK)


@api.route('/orders/up_paid_status', methods=['POST'])
@auth.login_required
def update_order_paid():
    """更新订单支付状态"""
    rid = request.json.get('rid')
    if not rid:
        abort(400)

    # 已支付，状态更新为待审核
    status = OrderStatus.PENDING_CHECK

    return _update_order_status(rid, status)


@api.route('/orders/up_sign_status', methods=['POST'])
@auth.login_required
def update_order_sign():
    """更新订单已签收状态"""
    rid = request.json.get('rid')
    if not rid:
        abort(400)

    return _update_order_status(rid, OrderStatus.SIGNED)


def _update_order_status(rid, status):
    """更新订单状态"""
    current_order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()

    if status == OrderStatus.PENDING_CHECK:  # 待审核
        # 验证订单状态, 仅未支付状态时，才可更新为待审核
        if current_order.status != OrderStatus.PENDING_PAYMENT:
            return custom_response('Order status is error!', 403, False)

        current_order.mark_checked_status()
    elif status == OrderStatus.SIGNED:  # 已签收
        current_order.mark_finished_status()

    db.session.commit()

    return full_response(R200_OK, {
        'rid': rid
    })


@api.route('/orders/create', methods=['POST'])
@auth.login_required
def create_order():
    """新增订单"""
    
    # 验证订单商品
    # {"rid":"","quantity":1,"deal_price":23, "discount_amount":0, "warehouse_id": 0}
    products = request.get_json().get('items')
    if products is None:
        return custom_response('Order product is empty!', 403, False)
    
    # 验证收货地址
    address_rid = request.get_json().get('address_rid')
    if address_rid is None:
        return custom_response('Address param is empty!', 403, False)
    address = Address.query.filter_by(user_id=g.current_user.id, serial_no=address_rid).first()
    if address is None:
        return custom_response("Address isn't exist!", 403, False)
    
    # 是否同步支付
    sync_pay = request.json.get('sync_pay')
    
    try:
        total_quantity = 0
        total_amount = 0
        total_discount = 0
        order_items = []
        for product in products:
            rid = product['rid']
            # 验证sku信息
            product_sku = ProductSku.query.filter_by(serial_no=rid).first()
            if not product_sku:
                return custom_response("商品不存在" % rid, 403, False)
            quantity = product.get('quantity')

            if product_sku.stock_count < quantity:
                return custom_response("库存不足", 403, False)

            # 同步减库存操作
            product_sku.stock_quantity -= quantity

            """
            # 验证库存
            warehouse_id = product.get('warehouse_id')
            if not warehouse_id:  # 未选择库房，则默认库房
                default_warehouse = Warehouse.find_default_warehouse(g.master_uid)
                if default_warehouse is None:
                    return custom_response("Default Warehouse isn't setting!", 403, False)
                warehouse_id = default_warehouse.id
            
            product_stock = product_sku.stocks.filter_by(warehouse_id=warehouse_id).first()
            if not product_stock or product_stock.available_count < quantity:
                return custom_response("[%s] inventory isn't enough!" % rid, 403, False)
            """
            warehouse_id = 0
            deal_price = float(product.get('deal_price'))
            discount_amount = Decimal(product.get('discount_amount', 0))
            
            order_items.append({
                'master_uid': g.master_uid,
                'warehouse_id': warehouse_id,
                'sku_id': product_sku.id,
                'sku_serial_no': rid,
                'quantity': quantity,
                'deal_price': deal_price,
                'discount_amount': discount_amount
            })
            
            total_quantity += quantity
            total_amount += deal_price * quantity
            total_discount += discount_amount

        outside_target_id = request.json.get('outside_target_id')
        freight = request.json.get('freight')
        affiliate_code = request.json.get('affiliate_code')
        # 总优惠金额
        discount_amount = request.json.get('discount_amount')
        from_client = request.json.get('from_client')
        if discount_amount:
            total_discount += discount_amount
        pay_amount = Decimal(total_amount) + freight - Decimal(total_discount)
        # 支付金额不能为负数
        if pay_amount < 0:
            pay_amount = 0.01

        order_serial_no = Order.make_unique_serial_no()
        append_dict = {
            'master_uid': g.master_uid,
            'user_id': g.current_user.id,
            'store_id': g.store_id,
            'serial_no': order_serial_no,
            'pay_amount': pay_amount,
            'total_amount': total_amount,
            'total_quantity': total_quantity,
            'affiliate_code': affiliate_code,
            'discount_amount': total_discount,
            'outside_target_id': outside_target_id,
            
            'address_id': address.id,
            'buyer_name': address.full_name,
            'buyer_tel': address.phone,
            'buyer_phone': address.mobile,
            'buyer_zipcode': address.zipcode,
            'buyer_address': address.street_address,
            'buyer_country': address.country.name,
            'buyer_province': address.province,
            'buyer_city': address.city,
            'buyer_town': address.town,
            'buyer_area': address.city
        }
        order_data = dict(request.get_json(), **append_dict)

        current_app.logger.warn(order_data)
        
        # 添加订单
        new_order = Order.create(order_data)
        db.session.add(new_order)
        
        # 保存订单明细
        for item in order_items:
            item['order_serial_no'] = order_serial_no
            order_item = OrderItem(order=new_order, **item)
            
            db.session.add(order_item)
        
        db.session.commit()
    except Exception as err:
        current_app.logger.warn('Create order failed: %s' % str(err))
        db.session.rollback()
        return custom_response('Create order failed: %s' % str(err), 400, False)

    # 触发任务
    _dispatch_sku_task(products)

    # 订单提交成功后，需删除本次购物车商品
    remove_order_cart.apply_async(args=[g.master_uid, order_serial_no])

    # 如使用优惠券，则更新状态
    if affiliate_code:
        update_coupon_status.apply_async(args=[g.master_uid, order_serial_no])

    if sync_pay:  # 同步返回客户端js支付所需参数
        if from_client == 1:  # 小程序
            pay_params = _wxapp_pay_params(order_serial_no, pay_amount)
            return full_response(R201_CREATED, {
                'order': new_order.to_json(),
                'pay_params': pay_params
            })

    return full_response(R201_CREATED, {
        'order': new_order.to_json()
    })


@api.route('/orders/logistic', methods=['POST'])
@auth.login_required
def track_logistic():
    """物流跟踪查询接口"""
    rid = request.json.get('rid')
    if not rid:
        abort(400)


@api.route('/orders/print', methods=['POST'])
@auth.login_required
def print_order():
    """打印订单"""
    rid = request.json.get('rid')
    if not rid:
        abort(400)


@api.route('/orders/signed', methods=['POST'])
@auth.login_required
def signed_order():
    """确认收货"""
    rid = request.json.get('rid')
    if not rid:
        abort(400)

    current_order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()

    # 标记签收
    current_order.mark_signed_status()

    db.session.commit()

    return full_response(R200_OK, {
        'order': current_order.to_json()
    })


@api.route('/orders/cancel', methods=['POST'])
@auth.login_required
def cancel_order():
    """取消订单"""
    rid = request.json.get('rid')
    if not rid:
        abort(400)

    current_order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    # 仅待支付、待审核、待发货订单，可取消
    if current_order.status not in [OrderStatus.PENDING_PAYMENT, OrderStatus.PENDING_CHECK,
                                    OrderStatus.PENDING_SHIPMENT]:
        abort(403)

    # 标记为取消
    current_order.mark_canceled_status()

    # todo: 取消订单，释放库存

    db.session.commit()

    return full_response(R200_OK, {
        'order': current_order.to_json()
    })
    

@api.route('/orders/delete', methods=['DELETE'])
@auth.login_required
def delete_order():
    """删除订单"""
    rid = request.json.get('rid')
    if not rid:
        abort(400)


@api.route('/orders/wx_prepay_sign', methods=['POST'])
@auth.login_required
def wxapp_prepay_sign():
    """微信小程序支付签名"""
    rid = request.json.get('rid')
    current_order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    # 验证订单状态
    if current_order.status != OrderStatus.PENDING_PAYMENT:
        return custom_response('Order status is error!', 403, False)

    pay_params = _wxapp_pay_params(rid, current_order.pay_amount)

    return full_response(R200_OK, pay_params)


@api.route('/orders/wx_pay/jsapi', methods=['POST'])
@auth.login_required
def pay_order_jsapi():
    """微信网页支付请求发起"""
    rid = request.json.get('rid')
    pay_type = request.json.get('pay_type', 1)  # 默认为微信支付
    openid = request.json.get('openid')
    data = {}
    if pay_type == 1:
        data = _js_wxpay_params(rid)

    return full_response(R200_OK, data)


def _wxapp_pay_params(rid, pay_amount, store_id=0):
    """小程序支付签名"""
    openid = g.current_user.openid
    cfg = current_app.config
    wxpay = WxPay(wx_app_id=cfg['WXPAY_APP_ID'], wx_mch_id=cfg['WXPAY_MCH_ID'], wx_mch_key=cfg['WXPAY_MCH_SECRET'],
                  wx_notify_url=cfg['WXPAY_NOTIFY_URL'])

    current_app.logger.warn('openid[%s],total_fee:[%s]' % (openid, str(int(pay_amount * 100))))
    prepay_result = wxpay.unified_order(
        body='D3IN未来店-小程序',
        openid=openid,  # 付款用户openid
        out_trade_no=rid,
        total_fee=str(int(pay_amount * 100)),  # total_fee 单位是 分， 100 = 1元
        trade_type='JSAPI')

    current_app.logger.warn('Unified order result: %s' % prepay_result)

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

    return pay_params


def _js_wxpay_params(rid):
    """获取客户端js支付所需参数"""
    current_order = Order.query.filter_by(master_uid=g.master_uid, serial_no=rid).first_or_404()
    # 验证订单状态
    if current_order.status != OrderStatus.PENDING_PAYMENT:
        return custom_response('Order status is error!', 403, False)
    
    # 微信支付初始化参数
    wx_pay = WxPay(
        wx_app_id=current_app.config['WECHAT_M_APP_ID'],
        wx_mch_id=current_app.config['WECHAT_M_PARTNER_ID'],
        wx_mch_key=current_app.config['WECHAT_M_KEY'],
        wx_notify_url=current_app.config['WECHAT_M_NOTIFY_URL'],
        ssl_key=current_app.config['WECHAT_M_SSL_KEY_PATH'],
        ssl_cert=current_app.config['WECHAT_M_SSL_CERT_PATH']
    )
    
    js_api_params = wx_pay.js_pay_api(
        openid='x2454sfd24d34g3424534',  # 付款用户openid
        body='D3IN 微商城',
        out_trade_no=rid,
        total_fee=str(current_order.pay_amount * 100),  # total_fee 单位是 分， 100 = 1元
        trade_type='MWEB'
        # scene_info='{"h5_info": {"type":"Wap","wap_url": "https://pay.qq.com","wap_name": "腾讯充值"}}'
    )
    
    return js_api_params


def _dispatch_sku_task(skus):
    """下单后同步更新商品库存数"""
    for sku in skus:
        product_sku = ProductSku.query.filter_by(serial_no=sku['rid']).first()
        sync_product_stock.apply_async(args=[product_sku.product_id])
