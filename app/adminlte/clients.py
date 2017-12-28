# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_babelex import gettext
from . import adminlte
from .. import db
from app.models import Client, ClientStatus
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, R400_BADREQUEST, Master, custom_response


@adminlte.route('/clients')
@adminlte.route('/clients/<int:page>')
def show_clients(page=1):
    """开放应用列表"""
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 0, type=int)

    if not status:
        query = Client.query
    else:
        query = Client.query.filter_by(status=status)

    paginated_clients = query.order_by(Client.created_at.desc()).paginate(page, per_page)

    return render_template('adminlte/clients/show_list.html',
                           paginated_clients=paginated_clients,
                           status=status,
                           top_menu='clients')


@adminlte.route('/clients/approved', methods=['POST'])
def approved_client():
    """审核某个应用"""
    app_key = request.form.get('app_key')
    if app_key is None:
        abort(404)
    
    client = Client.query.filter_by(master_uid=Master.master_uid(), app_key=app_key).first()
    if client is None:
        abort(404)

    client.status = ClientStatus.ENABLED
    
    db.session.commit()

    return custom_response(True, gettext('App has already approved!'))