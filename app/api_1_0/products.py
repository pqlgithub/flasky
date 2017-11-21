# -*- coding: utf-8 -*-
from . import api
from .utils import *

@api.route('/products')
def products():
    return "This is products list."