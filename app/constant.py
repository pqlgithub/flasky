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
    (1, gettext('Pending Review'), 'warning'),
    (5, gettext('Pending Arrival'), 'danger'),
    (10, gettext('Pending Storage'), 'primary'),
    (15, gettext('Finished'), 'success'),
    (-1, gettext('Canceled'), 'default')
)

# 采购付款状态
PURCHASE_PAYED = (
    (1, gettext('Available to Apply'), 'default'),
    (2, gettext('Unpaid'), 'warning'),
    (3, gettext('Finished Paid '), 'success')
)

# 入库状态
INWAREHOUSE_STATUS = (
    (1, gettext('Waiting In'), 'danger'),
    (2, gettext('Part'), 'warning'),
    (6, gettext('Finished'), 'success'),
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

# 仓库出入库操作类型
WAREHOUSE_OPERATION_TYPE = (
    (10, gettext('Purchase Storage')), # 采购入库
    (13, gettext('Returned Storage')), # 退货入库
    (16, gettext('Exchange Storage')), # 调仓入库
    (19, gettext('Manual Storage')), # 手动入库
    (20, gettext('Manual Out')), # 手动出库
    (24, gettext('Returned Out')), # 退货出库
)

# 排序代码简称
SORT_TYPE_CODE = {
    'ad': 'created_at',
    'ud': 'updated_at',
    'sq': 'current_count'
}