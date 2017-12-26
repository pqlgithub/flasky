# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from . import main
from .. import db
from app.models import Shop
from app.forms import H5mallForm
from ..utils import Master
from ..decorators import user_has, user_is


@main.route('/mall/setting', methods=['GET', 'POST'])
def setting_mall():
    """设置微商城基本信息"""
    form = H5mallForm()
    h5mall = Shop.query.filter_by(master_uid=Master.master_uid()).first()
    if form.validate_on_submit():
        if h5mall is None:
            h5mall = Shop(
                master_uid=Master.master_uid(),
                sn=Shop.make_unique_serial_no(),
                name=form.name.data,
                site_domain=form.site_domain.data,
                description=form.description.data
            )
            db.session.add(h5mall)
        else:
            h5mall.name = form.name.data
            h5mall.site_domain = form.site_domain.data
            h5mall.description = form.description.data

        db.session.commit()
        
        flash('Update shop setting is ok!', 'success')
        
        return redirect(url_for('.setting_mall'))
    
    if h5mall:
        form.name.data = h5mall.name
        form.site_domain.data = h5mall.site_domain
        form.description.data = h5mall.description
    
    return render_template('h5mall/setting.html',
                           form=form)