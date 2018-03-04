# -*- coding: utf-8 -*-

from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors, dashboard, order, product, brand, settings, user, \
                warehouse, purchase, finance, stat, file_manager, service, logistics, clients, \
                customer, market, h5mall, channel, wxapp
