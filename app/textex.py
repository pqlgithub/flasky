# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext

# 本地化语言对应关系
LOCAL_TEXTS = {
    # 用户默认创建目录
    'fx_default_directory': lazy_gettext('Default Directory'),
    'fx_product_directory': lazy_gettext('Product'),
    'fx_brand_directory': lazy_gettext('Brand'),
    'fx_category_directory': lazy_gettext('Category'),
    'fx_user_directory': lazy_gettext('User'),
    'fx_advertise_directory': lazy_gettext('Advertise'),

    # 默认权限
    'fx_admin_store': lazy_gettext('Admin Store'),
    'fx_admin_supplier': lazy_gettext('Admin Supplier'),
    'fx_admin_purchase': lazy_gettext('Admin Purchase'),
    'fx_admin_warehouse': lazy_gettext('Admin Warehouse'),
    'fx_admin_logistics': lazy_gettext('Admin Logistics'),
    'fx_admin_product': lazy_gettext('Admin Product'),
    'fx_admin_order': lazy_gettext('Admin Order'),
    'fx_admin_channel': lazy_gettext('Admin Channel'),
    'fx_admin_customer': lazy_gettext('Admin Customer'),
    'fx_admin_appstore': lazy_gettext('Admin Appstore'),
    'fx_admin_service': lazy_gettext('Admin Service'),
    'fx_admin_finance': lazy_gettext('Admin Finance'),
    'fx_admin_reports': lazy_gettext('Admin Reports'),
    'fx_admin_setting': lazy_gettext('Admin Setting'),
    'fx_admin_dashboard': lazy_gettext('Admin Dashboard'),

    # 默认币种
    'fx_currency_rmb': lazy_gettext('China Yuan'),
    'fx_currency_dollar': lazy_gettext('Dollars'),

}
