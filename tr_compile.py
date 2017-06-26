#!venv/bin/python
# -*- coding: utf-8 -*-
"""
    tr_compile.py
    ~~~~~~~~~~~~~

    编译目录的脚本
    :copyright: (c) 2017 by Mic.
"""

import os, sys

pybabel = 'venv/bin/pybabel'

os.system(pybabel + ' compile -d app/translations')
