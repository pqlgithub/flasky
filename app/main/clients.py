# -*- coding: utf-8 -*-
from flask import g, render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_babelex import gettext
from . import main
from .. import db
from app.models import Client, ClientStatus, Store
from app.forms import ClientForm, EditClientForm
from ..utils import Master, custom_response, make_unique_key, make_pw_hash
from ..decorators import user_has


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'settings',
        'sub_menu': 'clients'
    }

@main.route('/clients')
@main.route('/clients/<int:page>')
def show_clients(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 0, type=int)
    
    if not status:
        query = Client.query
    else:
        query = Client.query.filter_by(status=status)
    
    paginated_clients = query.order_by(Client.created_at.desc()).paginate(page, per_page)
    
    return render_template('clients/show_list.html',
                           paginated_clients=paginated_clients,
                           **load_common_data())


@main.route('/clients/<string:app_key>/manage', methods=['GET', 'POST'])
def manage_client(app_key):
    """管理应用"""
    client = Client.query.filter_by(master_uid=Master.master_uid(), app_key=app_key).first()
    if client is None:
        abort(404)

    form = EditClientForm(client)
    # 设置关联渠道
    stores = Store.query.filter_by(master_uid=Master.master_uid(), status=1).all()
    form.store_id.choices = [(store.id, '%s (%s)' % (store.name, store.platform_name)) for store in stores]
    if form.validate_on_submit():
        form.populate_obj(client)
        
        db.session.commit()
        
        flash('Update client is ok!', 'success')
        return redirect(url_for('.show_clients'))
    
    form.name.data = client.name
    form.store_id.data = client.store_id
    form.limit_times.data = client.limit_times
    form.receive_url.data = client.receive_url
    form.remark.data = client.remark
    
    return render_template('clients/client_detail.html',
                           client=client,
                           form=form,
                           **load_common_data())


@main.route('/clients/create', methods=['GET', 'POST'])
def create_client():
    """新增应用"""
    form = ClientForm()
    # 设置关联渠道
    stores = Store.query.filter_by(master_uid=Master.master_uid(), status=1).all()
    form.store_id.choices = [(store.id, '%s (%s)' % (store.name, store.platform_name)) for store in stores]
    if form.validate_on_submit():
        app_key = make_unique_key(20)
        app_secret = make_pw_hash(app_key)
        client = Client(
            master_uid=Master.master_uid(),
            app_key=app_key,
            app_secret=app_secret,
            name=form.name.data,
            store_id=form.store_id.data,
            limit_times=form.limit_times.data,
            receive_url=form.receive_url.data,
            remark=form.remark.data,
            status=ClientStatus.PENDING
        )
        db.session.add(client)
        
        flash('Add client is ok!', 'success')
        return redirect(url_for('.show_clients'))
    
    mode = 'create'
    return render_template('clients/create_and_edit.html',
                           mode=mode,
                           form=form,
                           **load_common_data())


@main.route('/clients/<string:app_key>/mark_disabled', methods=['POST'])
def mark_disabled(app_key):
    """禁用应用"""
    client = Client.query.filter_by(master_uid=Master.master_uid(), app_key=app_key).first()
    if client is None:
        abort(404)
    
    client.status = ClientStatus.DISABLED
    
    db.session.commit()
    
    return custom_response(True, gettext('App has already disabled!'))