# -*- coding: utf-8 -*-
from flask import g, session, current_app, request, redirect, url_for
from . import qa


@qa.route('/index')
def help_center():
    """帮助中心"""
    pass


@qa.route('/questions')
def show_questions():
    """问题列表"""
    pass


@qa.route('/solution')
def show_solution():
    """解决答案"""
    pass
