# -*- coding: utf-8 -*-

from flask import Blueprint

distribute = Blueprint('distribute', __name__)

from . import views, orders, products, errors
