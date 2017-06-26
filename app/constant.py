# -*- coding: utf-8 -*-
from flask_babelex import gettext

# 部门
DEPARTMENT = (
    {
        'id'  : 1,
        'name': '财务部'
    },
    {
        'id'  : 2,
        'name': '电商部'
    },
)

# 支持平台
SUPPORT_PLATFORM = (
    {
        'id'  : 1,
        'name': 'Mic'
    },
    {
        'id'  : 2,
        'name': 'JD京东'
    },
    {
        'id'  : 3,
        'name': 'Lazada'
    },
    {
        'id'  : 5,
        'name': 'Shopee'
    },
    {
        'id'  : 6,
        'name': '速卖通'
    },
)

# 采购到货状态
PURCHASE_STATUS = (
    (1, gettext('Unchecked'), 'warning'),
    (2, gettext('Checked'), 'warning'),
    (5, gettext('No Arrival'), 'danger'),
    (10, gettext('Waiting In'), 'primary'),
    (15, gettext('Finished'), 'success'),
    (-1, gettext('Canceled'), 'default')
)

# 采购付款状态
PURCHASE_PAYED = (
    (1, gettext('Apply Pay'), 'default'),
    (2, gettext('Waiting Pay'), 'warning'),
    (3, gettext('Finished Pay '), 'success')
)

# 收支类型
TRANSACT_TYPE = (
    (1, '收款'),
    (2, '付款')
)

# 收支相关单据
TRANSACT_TARGET_TYPE = (
    (1, gettext('Purchase')),
    (2, gettext('Order'))
)