# -*- coding: utf-8 -*-
from .initial import async_currency_rate, build_default_setting
from .weixin import refresh_component_token, refresh_authorizer_token, bind_wxa_tester, unbind_wxa_tester, \
    create_wxapi_appkey, create_banner_spot, reply_wxa_service
from .product import update_search_history, sync_product_stock, sync_supply_stats, sync_sku_stock
from .eorder import remove_order_cart, update_coupon_status
from .demo import add_together



