# -*- coding: utf-8 -*-
from flask import Blueprint

open = Blueprint('open', __name__)

from . import views, wechat, qiniu
