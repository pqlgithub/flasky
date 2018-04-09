# -*- coding: utf-8 -*-
from flask import g, session, current_app, request, redirect, url_for
from . import open


@open.route('/clients')
def show_clients():
    """
    应用列表
    :return:
    """
    pass


@open.route('/clients/create', methods=['GET', 'POST'])
def create_client():
    """
    添加应用
    :return:
    """
    pass


@open.route('/clients/update', methods=['GET', 'POST'])
def update_client():
    """
    更新应用信息
    :return:
    """
    pass


