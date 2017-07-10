# -*- coding: utf-8 -*-

from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, dashboard, errors, order, product, settings, user, \
                warehouse, purchase, finance, stat, file_manager, service, logistics, system
