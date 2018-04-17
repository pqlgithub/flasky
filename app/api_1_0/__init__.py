# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_cors import CORS

api = Blueprint('api', __name__)

# 存在跨域的问题
CORS(api)

from . import views, auth, tokens, users, errors, categories, products, orders, brands, \
    customers, shop, cart, address, accounts, search, market, wishlist, assets
