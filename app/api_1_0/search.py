# -*- coding: utf-8 -*-
from flask import request, abort, g, url_for
from app.models import User, Product

from .. import db
from . import api
from .auth import auth
from .utils import *


@api.route('/search/products')
def search_products():
    """搜索商品列表"""
    pass

