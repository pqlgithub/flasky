#!venv/bin/python
# -*- coding: utf-8 -*-
"""
    tr_init.py
    ~~~~~~~~~~~~

    添加语言到翻译目录
    :copyright: (c) 2017 by Mic.
"""
import os, sys

pybabel = 'venv/bin/pybabel'

if len(sys.argv) != 2:
    print("usage: tr_init <language-code>")
    sys.exit(1)

os.system(pybabel + ' extract -F babel.cfg -k lazy_gettext -o messages.pot app')
os.system(pybabel + ' init -i messages.pot -d app/translations -l ' + sys.argv[1])
os.unlink('messages.pot')
