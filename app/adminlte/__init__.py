# -*- coding: utf-8 -*-
from flask import Blueprint

adminlte = Blueprint('adminlte', __name__)

from . import views, system, clients, applications, address, settings, errors, weixin, qa
