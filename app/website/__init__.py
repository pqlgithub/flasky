# -*- coding: utf-8 -*-

from flask import Blueprint

site = Blueprint('site', __name__)

from . import web
