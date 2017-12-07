# -*- coding: utf-8 -*-
import datetime, time
from flask import g, render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_babelex import gettext
from flask_sqlalchemy import Pagination
from . import main
from .. import db
from app.models import Customer, CustomerGrade, User
from app.forms import CustomerForm, CustomerGradeForm, CustomerEditForm
from app.helpers import MixGenId
from ..utils import Master, custom_response, status_response, full_response, R200_OK
from ..decorators import user_has
from ..constant import CUSTOMER_STATUS


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'sub_menu': 'customers',
        'customer_status': CUSTOMER_STATUS
    }


@main.route('/customers/search', methods=['GET', 'POST'])
@login_required
def search_customers():
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    g = request.values.get('g', type=int)
    s = request.values.get('s', type=int)
    date = request.values.get('date', type=int)
    sk = request.values.get('sk', type=str, default='ad')
    
    builder = Customer.query.filter_by(master_uid=Master.master_uid())
    
    qk = qk.strip()
    if qk:
        current_app.logger.warn('Search customer [%s]!' % qk)
        builder = builder.whoosh_search(qk, or_=True, like=True)
    
    if g:
        builder = builder.filter_by(grade_id=g)
        
    if s:
        builder = builder.filter_by(status=s)
    
    if date:
        now = datetime.date.today()
        if date == 1:  # 今天之内
            start_time = time.mktime((now.year, now.month, now.day, 0, 0, 0, 0, 0, 0))
            end_time = time.time()
        if date == 2:  # 昨天之内
            dt = now - datetime.timedelta(days=1)
            start_time = time.mktime((dt.year, dt.month, dt.day, 0, 0, 0, 0, 0, 0))
            end_time = time.mktime((now.year, now.month, now.day, 0, 0, 0, 0, 0, 0))
        if date == 7:  # 7天之内
            dt = now - datetime.timedelta(days=7)
            start_time = time.mktime((dt.year, dt.month, dt.day, 0, 0, 0, 0, 0, 0))
            end_time = time.mktime((now.year, now.month, now.day, 0, 0, 0, 0, 0, 0))
        if date == 30:  # 30天之内
            dt = now - datetime.timedelta(days=30)
            start_time = time.mktime((dt.year, dt.month, dt.day, 0, 0, 0, 0, 0, 0))
            end_time = time.mktime((now.year, now.month, now.day, 0, 0, 0, 0, 0, 0))
        
        builder = builder.filter(Customer.created_at > start_time, Customer.created_at < end_time)
    
    current_app.logger.warn('Search customer --- sql: %s' % str(builder))
    
    customers = builder.order_by(Customer.created_at.desc()).all()
    
    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page
    
    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))
    
    paginated_customers = customers[start:end]
    
    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)
    
    return render_template('customers/search_result.html',
                           qk=qk,
                           sk=sk,
                           g=g,
                           s=s,
                           date=date,
                           paginated_customers=paginated_customers,
                           pagination=pagination)


@main.route('/customers')
@main.route('/customers/<int:page>')
@login_required
def show_customers(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_customers = Customer.query.filter_by(master_uid=Master.master_uid())\
        .filter(Customer.status.in_((1, 2))).order_by(Customer.created_at.desc()).paginate(page, per_page)

    grade_list = CustomerGrade.query.all()
    
    return render_template('customers/show_list.html',
                           paginated_customers=paginated_customers.items,
                           pagination=paginated_customers,
                           grade_list=grade_list,
                           **load_common_data())


@main.route('/customers/create', methods=['GET', 'POST'])
@login_required
def create_customer():
    """新增客户"""
    form = CustomerForm()
    form.grade_id.choices = [(grade.id, grade.name) for grade in CustomerGrade.query.all()]
    if form.validate_on_submit():
        
        # 首先添加用户
        user = User()
        
        user.email = form.customer_account.data
        user.username = form.sn.data
        user.password = form.customer_pwd.data
        user.time_zone = 'zh'
        user.id_type = 2
        
        db.session.add(user)
        
        # 然后，添加关联客户信息
        customer = Customer(
            master_uid=Master.master_uid(),
            name=form.name.data,
            sn=form.sn.data,
            grade_id=form.grade_id.data,
            province=form.province.data,
            city=form.city.data,
            area=form.area.data,
            street_address=form.street_address.data,
            zipcode=form.zipcode.data,
            mobile=form.mobile.data,
            phone=form.phone.data,
            email=form.email.data,
            qq=form.qq.data
        )
        customer.user = user
        
        db.session.add(customer)
        
        db.session.commit()
        
        flash('Add customer is ok!', 'success')
        return redirect(url_for('.show_customers'))
    else:
        current_app.logger.warn(form.errors)
    
    
    mode = 'create'
    form.sn.data = MixGenId.gen_customer_sn()
    return render_template('customers/create_and_edit.html',
                           mode=mode,
                           form=form,
                           **load_common_data())

@main.route('/customers/<string:sn>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(sn):
    customer = Customer.query.filter_by(sn=sn).first_or_404()
    if not Master.is_can(customer.master_uid):
        abort(401)
    
    form = CustomerEditForm()
    form.grade_id.choices = [(grade.id, grade.name) for grade in CustomerGrade.query.all()]
    if form.validate_on_submit():
        form.populate_obj(customer)
        
        db.session.commit()
        
        flash('Update customer is ok!', 'success')
        return redirect(url_for('.show_customers'))
    else:
        current_app.logger.warn(form.errors)
    
    mode = 'edit'
    form.name.data = customer.name
    form.grade_id.data = customer.grade_id
    form.province.data = customer.province
    form.city.data = customer.city
    form.area.data = customer.area
    form.street_address.data = customer.street_address
    form.zipcode.data = customer.zipcode
    form.mobile.data = customer.mobile
    form.phone.data = customer.phone
    form.email.data = customer.email
    form.qq.data = customer.qq
    
    return render_template('customers/create_and_edit.html',
                           mode=mode,
                           form=form,
                           **load_common_data())

@main.route('/customers/ajax_verify', methods=['POST'])
@login_required
def ajax_verify_customer():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        abort(404)
    
    try:
        selected_sns = []
        for sn in selected_ids:
            customer = Customer.query.filter_by(master_uid=Master.master_uid(), sn=sn).first()
            if customer:
                customer.status = 2
                
                selected_sns.append(sn)
        
        db.session.commit()
    except:
        db.session.rollback()
    
    return full_response(True, R200_OK, {
        'selected_sns': selected_sns
    })


@main.route('/customers/delete', methods=['POST'])
@login_required
def delete_customer():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete customer is null!', 'danger')
        abort(404)
    
    try:
        for sn in selected_ids:
            customer = Customer.query.filter_by(master_uid=Master.master_uid(), sn=sn).first()
            if customer:
                # 未物理删除，设置为禁用
                customer.status = -1
        
        db.session.commit()
        
        flash('Delete customer is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete customer is fail!', 'danger')
    
    return redirect(url_for('.show_customers'))


@main.route('/customer_grades')
@main.route('/customer_grades/<int:page>')
def show_grades(page=1):
    """客户等级"""
    per_page = request.args.get('per_page', 10, type=int)
    paginated_grades = CustomerGrade.query.filter_by(master_uid=Master.master_uid()) \
        .order_by(CustomerGrade.created_at.desc()).paginate(page, per_page)
    
    return render_template('customers/show_grades.html',
                           paginated_grades=paginated_grades,
                           **load_common_data())


@main.route('/customer_grades/create', methods=['GET', 'POST'])
def create_grade():
    form = CustomerGradeForm()
    if form.validate_on_submit():
        if CustomerGrade.query.filter_by(master_uid=Master.master_uid(), name=form.name.data).first():
            return custom_response(False, gettext('Name already exist!'))
        
        grade = CustomerGrade(
            master_uid=Master.master_uid(),
            name=form.name.data,
        )
        db.session.add(grade)
        db.session.commit()
        
        flash(gettext('Add Customer Grade is ok!'), 'success')
        return custom_response(True)
    
    mode = 'create'
    return render_template('customers/_modal_create.html',
                           mode=mode,
                           post_url=url_for('main.create_grade'),
                           form=form)


@main.route('/customer_grades/<int:id>/edit', methods=['GET', 'POST'])
def edit_grade(id):
    customer_grade = CustomerGrade.query.get_or_404(id)
    if customer_grade.master_uid != Master.master_uid():
        abort(401)
    
    form = CustomerGradeForm()
    if form.validate_on_submit():
        if customer_grade.name != form.name.data \
                and CustomerGrade.query.filter_by(master_uid=Master.master_uid(), name=form.name.data).first():
            return custom_response(False, gettext('Name already exist!'))
        
        customer_grade.name = form.name.data
        
        db.session.commit()
        
        flash(gettext('Update Customer Grade is ok!'), 'success')
        return custom_response(True)
    
    mode = 'edit'
    form.name.data = customer_grade.name
    return render_template('customers/_modal_create.html',
                           mode=mode,
                           post_url=url_for('main.edit_grade', id=id),
                           form=form)


@main.route('/customer_grades/delete', methods=['POST'])
def delete_grade():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete customer grade is null!', 'danger')
        abort(404)
    
    try:
        for id in selected_ids:
            grade = CustomerGrade.query.get_or_404(int(id))
            
            if not Master.is_can(grade.master_uid):
                abort(401)
            
            db.session.delete(grade)
        
        db.session.commit()
        
        flash('Delete grade is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete grade is fail!', 'danger')
    
    return redirect(url_for('.show_grades'))