# -*- coding: utf-8 -*-
import time, hashlib, re
from flask import g, render_template, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user
from flask_sqlalchemy import Pagination
from sqlalchemy.sql import func
from flask_babelex import gettext
import flask_whooshalchemyplus
from . import main
from .. import db, uploader
from ..utils import gen_serial_no
from app.models import Supplier, Brand
from app.forms import BrandForm
from ..utils import Master, full_response, status_response, custom_status, R200_OK, R201_CREATED, R204_NOCONTENT,\
    custom_response, import_product_from_excel
from ..decorators import user_has
from ..constant import SORT_TYPE_CODE, DEFAULT_REGIONS


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'products',
        'default_regions': DEFAULT_REGIONS
    }


@main.route('/brands/search', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def search_brands():
    """搜索品牌"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    sk = request.values.get('sk', type=str, default='ad')

    current_app.logger.debug('qk[%s], sk[%s]' % (qk, sk))

    builder = Brand.query.filter_by(master_uid=Master.master_uid())
    qk = qk.strip()
    if qk:
        builder = builder.whoosh_search(qk, like=True)

    brands = builder.order_by('created_at desc').all()

    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))

    paginated_brands = brands[start:end]

    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    return render_template('brands/search_result.html',
                           qk=qk,
                           sk=sk,
                           paginated_brands=paginated_brands,
                           pagination=pagination)

@main.route('/brands', methods=['GET', 'POST'])
@main.route('/brands/<int:page>', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def show_brands(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_brands = Brand.query.filter_by(master_uid=Master.master_uid()).order_by(Brand.created_at.desc()).paginate(page, per_page)
    return render_template('brands/show_list.html',
                           sub_menu='brands',
                           paginated_brands=paginated_brands,
                           **load_common_data())

@main.route('/brands/create', methods=['GET', 'POST'])
@login_required
def create_brand():
    """新增品牌"""
    form = BrandForm()
    if form.validate_on_submit():
        brand = Brand(
            master_uid=Master.master_uid(),
            supplier_id=form.supplier_id.data,
            name=form.name.data,
            features=form.features.data,
            description=form.description.data,
            logo_id=form.logo_id.data,
            banner_id=form.banner_id.data,
            sort_order=form.sort_order.data,
            status=form.status.data,
            is_recommended=form.is_recommended.data
        )
        db.session.add(brand)
        
        db.session.commit()
    
        flash('Add brand is ok!', 'success')
        
        return redirect(url_for('.show_brands'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'create'
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(
        1, 1000)
    return render_template('brands/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='brands',
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())
    

@main.route('/brands/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_supplier')
def edit_brand(id):
    brand = Brand.query.get_or_404(id)
    if brand.master_uid != Master.master_uid():
        abort(401)
    
    form = BrandForm()
    if form.validate_on_submit():
        form.populate_obj(brand)
        
        db.session.commit()

        flash('Edit brand is ok!', 'success')

        return redirect(url_for('.show_brands'))
    
    mode = 'edit'
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(
        1, 1000)
    
    form.name.data = brand.name
    form.supplier_id.data = brand.supplier_id
    form.features.data = brand.features
    form.description.data = brand.description
    form.logo_id.data = brand.logo_id
    form.banner_id.data = brand.banner_id
    form.sort_order.data = brand.sort_order
    form.status.data = brand.status
    form.is_recommended.data = brand.is_recommended
    
    return render_template('brands/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='brands',
                           brand=brand,
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/brands/delete', methods=['POST'])
@login_required
@user_has('admin_supplier')
def delete_brand():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete brand is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            brand = Brand.query.get_or_404(int(id))
            
            if brand.master_uid != Master.master_uid():
                abort(401)
            
            db.session.delete(brand)
        db.session.commit()

        flash('Delete brand is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete brand is fail!', 'danger')

    return redirect(url_for('.show_brands'))