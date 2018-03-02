# -*- coding: utf-8 -*-
import re
import json
import urllib.request
from flask import g, render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required
from flask_babelex import gettext
from . import main
from .. import db
from app.models import Store, User, UserIdType, STORE_TYPE, Banner, BannerImage, LINK_TYPES
from app.forms import StoreForm, BannerForm, BannerImageForm
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, Master, status_response
from ..helpers import MixGenId
from ..decorators import user_has


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'channels'
    }


@main.route('/stores')
@login_required
@user_has('admin_setting')
def show_stores():
    per_page = request.args.get('per_page', 20, type=int)
    builder = Store.query.filter_by(master_uid=Master.master_uid())
    paginated_stores = builder.order_by(Store.id.asc()).paginate(1, per_page)
    
    return render_template('stores/show_list.html',
                           sub_menu='stores',
                           paginated_stores=paginated_stores,
                           **load_common_data())


@main.route('/stores/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def create_store():
    form = StoreForm()
    form.type.choices = STORE_TYPE
    # 设置关联负责人
    user_list = User.query.filter_by(master_uid=Master.master_uid(), id_type=UserIdType.SUPPLIER).all()
    form.operator_id.choices = [(user.id, user.username) for user in user_list]
    
    if form.validate_on_submit():
        if Store.validate_unique_name(form.name.data, Master.master_uid(), form.platform.data):
            flash('Store name already exist!', 'danger')
            return redirect(url_for('.create_store'))
        
        store = Store(
            master_uid=Master.master_uid(),
            name=form.name.data,
            serial_no=MixGenId.gen_store_sn(),
            platform=form.platform.data,
            operator_id=form.operator_id.data,
            type=form.type.data,
            description=form.description.data,
            status=form.status.data
        )
        db.session.add(store)
        
        db.session.commit()

        flash('Add store is success!', 'success')
        
        return redirect(url_for('.show_stores'))

    return render_template('stores/create_and_edit.html',
                           form=form,
                           sub_menu='stores',
                           **load_common_data())


@main.route('/stores/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_setting')
def edit_store(id):
    store = Store.query.get_or_404(id)
    if not Master.is_can(store.master_uid):
        abort(401)
    
    form = StoreForm()
    form.type.choices = STORE_TYPE
    
    user_list = User.query.filter_by(master_uid=Master.master_uid(), id_type=UserIdType.SUPPLIER).all()
    form.operator_id.choices = [(user.id, user.username) for user in user_list]
    if form.validate_on_submit():
        old_store = Store.validate_unique_name(form.name.data, Master.master_uid(), form.platform.data)
        if old_store and old_store.id != id:
            flash('Store name already exist!', 'danger')
            return redirect(url_for('.edit_store', id=id))

        form.populate_obj(store)
        
        db.session.commit()

        flash('Edit store is success!', 'success')
        return redirect(url_for('.show_stores'))

    # 填充数据
    form.name.data = store.name
    form.platform.data = store.platform
    form.operator_id.data = store.operator_id
    form.type.data = store.type
    form.description.data = store.description
    form.status.data = store.status

    return render_template('stores/create_and_edit.html',
                           form=form,
                           sub_menu='stores', **load_common_data())


@main.route('/stores/delete', methods=['POST'])
@user_has('admin_setting')
def delete_store():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete store is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            store = Store.query.get_or_404(int(id))
            if Master.is_can(store.master_uid):
                db.session.delete(store)
        db.session.commit()
        
        flash('Delete store is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete store is fail!', 'danger')
    
    return redirect(url_for('.show_stores'))


@main.route('/banners', methods=['GET', 'POST'])
@main.route('/banners/<int:page>', methods=['GET', 'POST'])
@user_has('admin_setting')
def show_banners(page=1):
    """banner列表"""
    per_page = request.args.get('per_page', 20, type=int)
    
    if request.method == 'POST':
        # 搜索
        qk = request.values.get('qk')
        sk = request.values.get('sk')
        p = request.values.get('p', type=int)
        
        builder = BannerImage.query.filter_by(master_uid=Master.master_uid())
        if p:
            builder = builder.filter_by(banner_id=p)
    
        paginated_banners = builder.order_by(BannerImage.created_at.desc()).paginate(page, per_page)
        
        return render_template('banners/search_result.html',
                               paginated_banners=paginated_banners,
                               p=p,
                               qk=qk,
                               sk=sk)
    
    # 正常列表
    builder = BannerImage.query.filter_by(master_uid=Master.master_uid())
    paginated_banners = builder.order_by(BannerImage.created_at.desc()).paginate(page, per_page)
    
    spot_list = Banner.query.filter_by(master_uid=Master.master_uid()).all()
    
    return render_template('banners/show_list.html',
                           sub_menu='banners',
                           spot_list=spot_list,
                           paginated_banners=paginated_banners,
                           **load_common_data())


@main.route('/banners/create', methods=['GET', 'POST'])
@user_has('admin_setting')
def create_banner():
    """新增banner"""
    form = BannerImageForm()
    spot_list = Banner.query.filter_by(master_uid=Master.master_uid()).all()
    form.spot_id.choices = [(spot.id, spot.name) for spot in spot_list]

    form.type.choices = LINK_TYPES
    if form.validate_on_submit():
        banner_image = BannerImage(
            master_uid=Master.master_uid(),
            banner_id=form.spot_id.data,
            title=form.title.data,
            type=form.type.data,
            link=form.link.data,
            image_id=form.image_id.data,
            sort_order=form.sort_order.data,
            description=form.description.data,
            status=form.status.data
        )
        db.session.add(banner_image)
        db.session.commit()
        
        flash('Add banner is ok!', 'success')
        
        return redirect(url_for('.show_banners'))
    else:
        current_app.logger.warn(form.errors)
    
    mode = 'create'
    return render_template('banners/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='banners',
                           **load_common_data())


@main.route('/banners/<int:id>/edit', methods=['GET', 'POST'])
@user_has('admin_setting')
def edit_banner(id):
    banner_image = BannerImage.query.get_or_404(id)
    if not Master.is_can(banner_image.master_uid):
        abort(401)
        
    form = BannerImageForm()
    spot_list = Banner.query.filter_by(master_uid=Master.master_uid()).all()
    form.spot_id.choices = [(spot.id, spot.name) for spot in spot_list]
    form.type.choices = LINK_TYPES
    if form.validate_on_submit():
        banner_image.banner_id = form.spot_id.data
        form.populate_obj(banner_image)
        
        db.session.commit()

        flash('Edit banner is ok!', 'success')

        return redirect(url_for('.show_banners'))
        
    mode = 'edit'
    
    form.spot_id.data = banner_image.banner_id
    form.title.data = banner_image.title
    form.link.data = banner_image.link
    form.type.data = banner_image.type
    form.image_id.data = banner_image.image_id
    form.sort_order.data = banner_image.sort_order
    form.description.data = banner_image.description
    form.status.data = banner_image.status
    
    return render_template('banners/create_and_edit.html',
                           form=form,
                           mode=mode,
                           banner=banner_image,
                           sub_menu='banners',
                           **load_common_data())
    

@main.route('/banners/delete', methods=['POST'])
@user_has('admin_setting')
def delete_banner():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete banner is null!', 'danger')
        abort(404)
    
    try:
        for id in selected_ids:
            banner_image = BannerImage.query.get_or_404(int(id))
            if Master.is_can(banner_image.master_uid):
                db.session.delete(banner_image)
        db.session.commit()
        
        flash('Delete banner is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete banner is fail!', 'danger')
    
    return redirect(url_for('.show_banners'))


@main.route('/banner_spot/create', methods=['GET', 'POST'])
@user_has('admin_setting')
def create_spot():
    """新增banner位置"""
    form = BannerForm()
    if form.validate_on_submit():
        spot = Banner(
            master_uid=Master.master_uid(),
            serial_no=MixGenId.gen_letters(12),
            name=form.name.data,
            width=form.width.data,
            height=form.height.data,
            status=1
        )
        db.session.add(spot)
        db.session.commit()
        
        flash('Add banner spot is ok!', 'success')
        
        return status_response(True, R201_CREATED)
    
    mode = 'create'
    return render_template('banners/_modal_spot_create.html',
                           post_url=url_for('.create_spot'),
                           form=form)