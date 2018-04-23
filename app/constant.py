# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext


# 开通的国家
SUPPORT_COUNTRIES = (
    (1, 'zh', lazy_gettext('China')),
    (2, 'en', lazy_gettext('USA')),
)

# 支持的语言 Language
SUPPORT_LANGUAGES = (
    (1, 'zh', '简体中文'),
    (2, 'en', 'English'),
    (3, 'th', 'Thailand'),
    (9, 'zh_TW', '繁體中文')
)

# 支持的币种 currencies
SUPPORT_CURRENCIES = (
    (1, 'CNY'),
    (2, 'USD'),
    (3, 'JPY'),
    (4, 'SGD'),
    (5, 'THB'),
    (6, 'KRW'),
    (7, 'SUR'),
    (8, 'PHP')
)

# 默认币种配置
DEFAULT_CURRENCIES = (
    {
        'title': 'fx_currency_rmb',
        'code': 'CNY',
        'symbol_left': '￥',
        'symbol_right': '',
        'decimal_place': '2',
        'value': 1
    },
    {
        'title': 'fx_currency_dollar',
        'code': 'USD',
        'symbol_left': '$',
        'symbol_right': '',
        'decimal_place': '2',
        'value': 6.67
    }
)

# 部门
DEPARTMENT = (
    {
        'id': 1,
        'name': '财务部'
    },
    {
        'id': 2,
        'name': '电商部'
    },
)

# 支持平台
SUPPORT_PLATFORM = (
    {
        'id': 1,
        'name': '微信小程序'
    },
    {
        'id': 10,
        'name': '自营实体店'
    },
    {
        'id': 31,
        'name': '京东'
    },
    {
        'id': 31,
        'name': '淘宝'
    }
)

# 区域划分
DEFAULT_REGIONS = (
    {
        'id': 1,
        'name': lazy_gettext('Overseas')
    },
    {
        'id': 2,
        'name': lazy_gettext('Domestic')
    }
)


# 默认物流
DEFAULT_EXPRESS = {
    'name': 'Default Express',
    'contact_name': 'eLing',
    'contact_mobile': '13866666666',
    'contact_phone': '13866666666',
    'description': 'This is default express!',
    'is_default': True,
    'code': 'default'
}

# 默认供应商
DEFAULT_SUPPLIER = {
    'short_name': 'Default Supplier',
    'full_name': 'Default Supplier Full Name',
    'start_date': '2017-01-01',
    'end_date': '2027-01-01',
    'contact_name': 'Michose',
    'address': "Michose's address",
    'phone': '13866666666',
    'remark': 'This is default supplier!',
    'is_default': True,
}

# 默认附件
DEFAULT_ASSET = {
    'filepath': 'static/img/default-logo-180x180.png',
    'filename': 'mic_logo180x180.jpg',
    'width': 180,
    'height': 180,
    'mime': 'image/jpeg',
    'is_default': True
}

# 默认目录
DEFAULT_DIRECTORY = {
    'name': 'Default Directory',
    'is_default': True
}

# 采购到货状态
PURCHASE_STATUS = (
    (1, gettext('Pending Review'), lazy_gettext('Pending Review'), 'warning'),
    (5, gettext('Pending Arrival'), lazy_gettext('Pending Arrival'), 'danger'),
    (10, gettext('Pending Storage'), lazy_gettext('Pending Storage'), 'primary'),
    (15, gettext('Finished'), lazy_gettext('Finished'), 'success'),
    (-1, gettext('Canceled'), lazy_gettext('Canceled'), 'default')
)

# 采购付款状态
PURCHASE_PAYED = (
    (1, gettext('Available to Apply'), lazy_gettext('Available to Apply'), 'danger'),
    (2, gettext('Unpaid'), lazy_gettext('Unpaid'), 'warning'),
    (3, gettext('Finished Paid '), lazy_gettext('Finished Paid '), 'success')
)

# 入库状态
INWAREHOUSE_STATUS = (
    (1, lazy_gettext('Waiting In'), 'danger'),
    (2, lazy_gettext('Part'), 'warning'),
    (6, lazy_gettext('Finished'), 'success'),
)

OUTWAREHOUSE_STATUS = (
    (1, lazy_gettext('UnOut Stock'), 'danger'),
    (2, lazy_gettext('Outing Stock'), 'danger'),
    (3, lazy_gettext('Outed Stock'), 'success')
)

# 收支类型
TRANSACT_TYPE = (
    (1, '收款'),
    (2, '付款')
)

# 收支相关单据
TRANSACT_TARGET_TYPE = (
    (1, lazy_gettext('Purchase')),
    (2, lazy_gettext('Order'))
)

# 仓库出入库操作类型
WAREHOUSE_OPERATION_TYPE = (
    (10, lazy_gettext('Purchase Storage')), # 采购入库
    (13, lazy_gettext('Returned Storage')), # 退货入库
    (16, lazy_gettext('Exchange Storage')), # 调仓入库
    (19, lazy_gettext('Manual Storage')), # 手动入库
    (20, lazy_gettext('Manual Out')), # 手动出库
    (21, lazy_gettext('Order Out')), # 订单出库
    (30, lazy_gettext('Returned Out')), # 退货出库
)

# 排序代码简称
SORT_TYPE_CODE = {
    'ad': 'created_at',
    'ud': 'updated_at',
    'sq': 'current_count',
    'ed': 'end_date',
    'dd': 'arrival_date',
    'sc': 'sku_count',
    'pt': 'purchase_times',
    'pa': 'purchase_amount'
}

# 行业范围
SUPPORT_DOMAINS = (
    (1, lazy_gettext('Retail')),
    (2, lazy_gettext('Services'))
)


# 默认权限列表
DEFAULT_ACLIST = (
    ('admin_store', 'fx_admin_store'),
    ('admin_supplier', 'fx_admin_supplier'),
    ('admin_purchase', 'fx_admin_purchase'),
    ('admin_warehouse', 'fx_admin_warehouse'),
    ('admin_logistics', 'fx_admin_logistics'),
    ('admin_product', 'fx_admin_product'),
    ('admin_order', 'fx_admin_order'),
    ('admin_channel', 'fx_admin_channel'),
    ('admin_customer', 'fx_admin_customer'),
    ('admin_appstore', 'fx_admin_appstore'),
    ('admin_service', 'fx_admin_service'),
    ('admin_finance', 'fx_admin_finance'),
    ('admin_reports', 'fx_admin_reports'),
    ('admin_setting', 'fx_admin_setting'),
    ('admin_dashboard', 'fx_admin_dashboard')
)

# 默认图片
DEFAULT_IMAGES = {
    'cover': {
        'view_url': '/static/img/no_img100x100.png'
    }
}

# 产品数量单位
PRODUCT_DEFAULT_UNIT = (
    (1, lazy_gettext('piece'))
)

# 分销商客户的状态
CUSTOMER_STATUS = [
    (2, lazy_gettext('Enabled'), 'success'),
    (1, lazy_gettext('Pending Approval'), 'danger'),
    (-1, lazy_gettext('Disabled'), 'default'),
]

# 分销价格模板
DISCOUNT_TEMPLET_TYPES = (
    (1, lazy_gettext('By Category')),
    (2, lazy_gettext('By Brand'))
)


# 服务市场应用类型
# 营销插件、渠道应用、供销管理、主题皮肤
SERVICE_TYPES = (
    (1, lazy_gettext('Marketing')),
    (2, lazy_gettext('Channel Application')),
    (3, lazy_gettext('Supply Management')),
    (4, lazy_gettext('Theme'))
)


# 支付方式
PAY_TYPES = (
    (1, lazy_gettext('Wechat Pay')),
    (2, lazy_gettext('Alipay')),
    (3, lazy_gettext('Quick Pay')),
    (4, lazy_gettext('Apple Pay'))
)


# 导出采购单头格式 / 采购单对应的字段
PURCHASE_EXCEL_FIELDS = {
    'serial_no': gettext('Purchase Serial'),
    'product_name': gettext('Product Name'),
    'product_sku': gettext('Product SKU'),
    'quantity_sum': gettext('Purchase Quantity'),
    'in_quantity': gettext('Arrival Quantity'),
    'freight': gettext('Freight'),
    'extra_charge': gettext('Other Charge'),
    'total_amount': gettext('Total Amount'),
    'warehouse': gettext('Warehouse'),
    'supplier': gettext('Supplier'),
    'contact_name': gettext('Contact Name'),
    'phone': gettext('Contact Phone'),
    'express_no': gettext('Express No'),
    'created_at': gettext('Add Date'),
    'arrival_at': gettext('Arrival Date'),
    'status': gettext('Arrival Status'),
    'remark': gettext('Remark')
}

# 导入/导出订单物流信息
ORDER_EXPRESS_FIELDS = {
    # 第三方订单号
    'outside_target_id': '订单号',
    'express_name': '物流服务商',
    'express_no': '快递单号'
}

# 导入/导出订单格式（Mixpus）
MIXPUS_ORDER_FIELDS = {
    'serial_no': '订单号',
    'store_name': '店铺',
    'status': '订单状态',
    'product_id':  '商品ID',
    'product_name': '商品名称',
    's_model': '商品规格',
    'deal_price': '商品销售单价',
    'freight': '运费',
    'total_quantity': '实际成交数量',
    'total_amount': '商品销售总额',
    'discount_amount': '优惠总金额',
    'created_at': '下单时间',
    'express_at': '发货时间',
    'received_at': '收货时间',
    'buyer_name': '收件人',
    'buyer_phone': '收件人手机',
    'buyer_address': '收件人地址',
    'buyer_remark': '买家留言',
    'express_name': '物流服务商',
    'express_no': '快递单号'
}

# 导入/导出订单格式对应（第三方）
ORDER_EXCEL_FIELDS = {
    'store_name': '店铺',
    'store_id': '店铺ID',
    'order_serial_no': '订单号',
    'order_status': '订单状态',
    'order_product_list': '订单商品清单',
    'order_product_id':  'Item ID',
    'order_product_name': '商品名称',
    's_model': '商品规格',
    'product_status': '商品状态',
    'outside_product_serial': 'hmall商品编号',
    'shop_product_id': '商城产品ID',
    'shop_goods_id': '商城商品ID',
    'cost_price': '成本单价',
    'sale_price': '商品销售单价',
    'freight': '运费',
    'quantity': '商品数量',
    'deal_quantity': '实际成交数量',
    'total_amount': '商品销售总额',
    'use_discount': '使用优惠券',
    'platform_discount_amount': '平台优惠金额',
    'store_discount_amount': '店铺优惠金额',
    'discount_total_amount': '优惠总金额',
    'point': '积分',
    'voice_amount': '开票金额',
    'category_level1_id': '一类ID',
    'category_level2_id': '二类ID',
    'category_level3_id': '三类ID',
    'category_level1_name': '一类',
    'category_level2_name': '二类',
    'category_level3_name': '三类',
    'pay_away': '支付类型',
    'ordered_at': '下单时间',
    'payed_at': '支付时间',
    'express_at': '发货时间',
    'received_at': '收货时间',
    'finished_at': '订单完成时间',
    'buyer_phone': '购买人手机',
    'buyer_name': '收件人',
    'buyer_mobile': '收件人手机',
    'buyer_address': '收件人地址',
    'express_id': '物流服务商',
    'express_no': '快递单号',
    'buyer_remark': '买家留言',
    'store_goods_id': '店铺商品ID',
    'voice_info': '发票信息',
    'store_product_id': '店铺产品ID'
}

# 华住订单状态
HUAZHU_ORDER_STATUS = [
    (-1, '订单已取消'),
    (15, '已发货'),
    (5, '已付款请耐心等待'),
    (17, '已签收'),
    (18, '已退款'),
    (20, '已完成'),
]

# 华住订单物流
HUAZHU_EXPRESS_FIELDS = {
    'serial_no': '订单号',
    'express_name': '物流服务商',
    'express_no': '快递单号'
}
