# -*- coding: utf-8 -*-
from . import api
from .utils import *

@api.route('/brands')
def brands():
    return "This is brands list."