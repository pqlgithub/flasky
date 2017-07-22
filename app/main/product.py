# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user
from flask_sqlalchemy import Pagination
from . import main
from .. import db
from ..utils import gen_serial_no
from app.models import Product, Supplier, Category, ProductSku, ProductStock, WarehouseShelve, Asset, SupplyStats
from app.forms import ProductForm, SupplierForm, CategoryForm, EditCategoryForm, ProductSkuForm
from ..utils import Master, full_response, status_response, custom_status, R200_OK, R201_CREATED, R204_NOCONTENT, R500_BADREQUEST
from ..decorators import user_has
from ..constant import SORT_TYPE_CODE


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'products'
    }

@main.route('/products')
@main.route('/products/<int:page>')
@login_required
@user_has('admin_product')
def show_products(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    builder = Product.query.filter_by(master_uid=Master.master_uid())

    paginated_result = builder.order_by('created_at desc').paginate(page, per_page)

    return render_template('products/show_list.html',
                           sub_menu='products',
                           paginated_products=paginated_result.items,
                           pagination=paginated_result,
                           **load_common_data())


@main.route('/products/search', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def search_products():
    """支持全文索引搜索产品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    sk = request.values.get('sk', type=str, default='ad')

    current_app.logger.debug('qk[%s], sk[%s]' % (qk, sk))

    builder = Product.query.filter_by(master_uid=Master.master_uid())
    if qk:
        builder = builder.whoosh_search(qk, like=True)

    products = builder.order_by('%s desc' % SORT_TYPE_CODE[sk]).all()

    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))

    paginated_products = products[start:end]

    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    return render_template('products/search_result.html',
                           qk=qk,
                           sk=sk,
                           paginated_products=paginated_products,
                           pagination=pagination)


@main.route('/products/ajax_search', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def ajax_search_products():
    """搜索产品,满足采购等选择产品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    supplier_id = request.values.get('supplier_id')
    qk = request.values.get('qk')
    if request.method == 'POST':
        builder = ProductSku.query.filter_by(master_uid=Master.master_uid(), supplier_id=supplier_id)
        if qk:
            builder = builder.whoosh_search(qk, like=True)

        skus = builder.order_by('created_at desc').all()

        # 构造分页
        total_count = builder.count()
        if page == 1:
            start = 0
        else:
            start = (page - 1) * per_page
        end = start + per_page

        current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))

        paginated_skus = skus[start:end]

        pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

        return render_template('purchases/purchase_tr_time.html',
                               paginated_skus=paginated_skus,
                               pagination=pagination)

    skus = ProductSku.query.filter_by(master_uid=Master.master_uid(), supplier_id=supplier_id).order_by('created_at desc').all()

    return render_template('purchases/purchase_modal.html',
                           supplier_id=supplier_id,
                           skus=skus)


@main.route('/products/skus', methods=['POST'])
@login_required
@user_has('admin_product')
def ajax_find_skus():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        return status_response(False, custom_status('Select id is null!'))

    selected_ids = [int(sku_id) for sku_id in selected_ids]
    skus = ProductSku.query.filter(ProductSku.id.in_(selected_ids)).all()

    sku_list = [sku.to_json() for sku in skus]

    return full_response(True, R200_OK, sku_list)


@main.route('/products/ajax_select', methods=['POST'])
@login_required
@user_has('admin_product')
def ajax_select_products():
    """搜索库存产品,满足下单/出库等选择产品"""
    paginated_stocks = None
    wh_id = request.form.get('wh_id')
    t = request.form.get('t', 'stock')
    page = request.values.get('page', 1, type=int)

    query = ProductStock.query
    if wh_id:
        query = query.filter_by(warehouse_id=wh_id)
        paginated_stocks = query.order_by('created_at desc').paginate(page, 10)

    return render_template('products/select_product_modal.html',
                           paginated_stocks=paginated_stocks,
                           wh_id=wh_id,
                           t=t)

@main.route('/products/ajax_submit_result', methods=['POST'])
@login_required
@user_has('admin_product')
def ajax_submit_result():
    """返回已选定产品的结果"""
    wh_id = request.form.get('wh_id')
    t = request.form.get('t', 'stock')

    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        return 'Select id is null!'

    selected_ids = [int(stock_id) for stock_id in selected_ids]
    stock_products = ProductStock.query.filter(ProductStock.id.in_(selected_ids)).all()

    # 货架
    warehouse_shelves = WarehouseShelve.query.filter_by(warehouse_id=wh_id).all()

    tpl = 'products/select_result.html'
    if t == 'order':
        tpl = 'products/select_result_for_order.html'
    return render_template(tpl,
                           stock_products=stock_products,
                           warehouse_shelves=warehouse_shelves)



@main.route('/products/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def create_product():
    form = ProductForm()
    if form.validate_on_submit():
        # 设置默认值
        if not form.cover_id.data:
            default_cover = Asset.query.filter_by(is_default=True).first()
            form.cover_id.data = default_cover.id

        product = Product(
            master_uid=Master.master_uid(),
            serial_no=Product.make_unique_serial_no(form.serial_no.data),
            supplier_id=form.supplier_id.data,
            name=form.name.data,
            cover_id=form.cover_id.data,
            cost_price=form.cost_price.data,
            sale_price=form.sale_price.data,
            s_weight=form.s_weight.data,
            s_length=form.s_length.data,
            s_width=form.s_width.data,
            s_height=form.s_height.data,
            from_url=form.from_url.data,
            status=form.status.data,
            description=form.description.data
        )
        db.session.add(product)

        # 更新所属分类
        if form.category_id.data:
            categories = []
            categories.append(Category.query.get(form.category_id.data))

            product.update_categories(*categories)

        db.session.commit()

        return redirect(url_for('.show_products'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'create'
    form.serial_no.data = Product.make_unique_serial_no(gen_serial_no())

    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(1, 1000)

    return render_template('products/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='products',
                           product=None,
                           paginated_categories=paginated_categories,
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm()
    if form.validate_on_submit():
        form.populate_obj(product)

        # 更新所属分类
        if form.category_id.data:
            categories = []
            categories.append(Category.query.get(form.category_id.data))

            product.update_categories(*categories)

        db.session.commit()

        return redirect(url_for('.show_products'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'edit'

    form.serial_no.data = product.serial_no
    form.supplier_id.data = product.supplier_id
    form.name.data = product.name
    form.cover_id.data = product.cover_id
    form.cost_price.data = product.cost_price
    form.sale_price.data = product.sale_price
    form.s_weight.data = product.s_weight
    form.s_length.data = product.s_length
    form.s_width.data = product.s_width
    form.s_height.data = product.s_height
    form.from_url.data = product.from_url
    form.status.data = product.status
    form.description.data = product.description

    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(1, 1000)

    return render_template('products/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='products',
                           product=product,
                           paginated_categories=paginated_categories,
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/products/delete', methods=['POST'])
@login_required
@user_has('admin_product')
def delete_product():
    pass

@main.route('/products/<int:id>/skus')
@user_has('admin_product')
def show_skus(id):
    product_skus = ProductSku.query.filter_by(product_id=id).all()
    return render_template('/products/show_skus.html',
                           product_skus=product_skus)


@main.route('/products/<int:id>/add_sku', methods=['GET', 'POST'])
@user_has('admin_product')
def add_sku(id):
    product = Product.query.get_or_404(id)
    form = ProductSkuForm()
    if form.validate_on_submit():
        # 设置默认值
        if not form.sku_cover_id.data:
            default_cover = Asset.query.filter_by(is_default=True).first()
            form.sku_cover_id.data = default_cover.id

        sku = ProductSku(
            product_id=id,
            supplier_id=product.supplier_id,
            master_uid=Master.master_uid(),
            serial_no=Product.make_unique_serial_no(form.serial_no.data),
            cover_id=form.sku_cover_id.data,
            s_model=form.s_model.data,
            s_weight=form.s_weight.data,
            cost_price=form.cost_price.data,
            sale_price=form.sale_price.data,
            remark=form.remark.data
        )
        db.session.add(sku)

        db.session.commit()

        return full_response(True, R201_CREATED, sku.to_json())

    mode = 'create'
    form.serial_no.data = Product.make_unique_serial_no(gen_serial_no())
    form.cost_price.data = product.cost_price
    form.sale_price.data = product.sale_price
    form.s_weight.data = product.s_weight
    return render_template('products/modal_sku.html',
                           form=form,
                           mode=mode,
                           post_sku_url=url_for('.add_sku', id=id),
                           product=product)


@main.route('/products/<int:id>/edit_sku/<int:s_id>', methods=['GET', 'POST'])
@user_has('admin_product')
def edit_sku(id, s_id):
    product = Product.query.get_or_404(id)
    sku = ProductSku.query.get_or_404(s_id)
    form = ProductSkuForm()
    if form.validate_on_submit():
        sku.cover_id = form.sku_cover_id.data
        sku.s_model = form.s_model.data
        sku.s_weight = form.s_weight.data
        sku.cost_price = form.cost_price.data
        sku.sale_price = form.sale_price.data
        sku.remark = form.remark.data

        db.session.commit()

        return full_response(True, R201_CREATED, sku.to_json())

    mode = 'edit'

    form.serial_no.data = sku.serial_no
    form.sku_cover_id.data = sku.cover_id
    form.cost_price.data = sku.cost_price
    form.sale_price.data = sku.sale_price
    form.s_model.data = sku.s_model
    form.s_weight.data = sku.s_weight
    form.remark.data = sku.remark

    return render_template('products/modal_sku.html',
                           form=form,
                           mode=mode,
                           product=product,
                           post_sku_url=url_for('.edit_sku', id=id, s_id=s_id),
                           sku=sku)


@main.route('/products/<int:s_id>/delete_sku', methods=['POST'])
@user_has('admin_product')
def delete_sku(s_id):
    try:
        sku = ProductSku.query.get_or_404(s_id)
        db.session.delete(sku)
        db.session.commit()

        return full_response(True, R204_NOCONTENT, {'id': s_id})
    except:
        db.session.rollback()
        return full_response(True, custom_status('Delete sku is failed!', 500))


@main.route('/categories')
@main.route('/categories/<int:page>')
@login_required
@user_has('admin_product')
def show_categories(page=1):
    per_page = request.args.get('per_page', 15, type=int)

    total = Category.query.filter_by(master_uid=Master.master_uid()).count()

    categories = Category.always_category(path=0, page=page, per_page=per_page, uid=Master.master_uid())

    paginated_categories = []
    for cate in categories:
        category = {
            'id': cate.id,
            'name': cate.name,
            'sort_order': cate.sort_order,
            'status': cate.status
        }
        paginated_categories.append(category)

    pagination = Pagination(query=None, page=1, per_page=per_page, total=total, items=None)
    return render_template('categories/show_list.html',
                           paginated_categories=paginated_categories,
                           pagination=pagination,
                           sub_menu='categories',
                           **load_common_data())


@main.route('/categories/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            master_uid=Master.master_uid(),
            name=form.name.data,
            pid=form.pid.data,
            sort_order=form.sort_order.data,
            description=form.description.data,
            status=form.status.data,
        )
        db.session.add(category)
        db.session.commit()

        # rebuild category path
        Category.repair_categories(category.pid)

        flash('Add category is ok!', 'success')

        return redirect(url_for('.show_categories'))

    mode = 'create'
    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    return render_template('categories/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='categories',
                           category=None,
                           paginated_categories=paginated_categories,
                           **load_common_data())


@main.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = EditCategoryForm(category)
    if form.validate_on_submit():
        form.populate_obj(category)

        db.session.commit()

        # rebuild category path
        Category.repair_categories(category.pid)

        flash('Edit category is ok!', 'success')

        return redirect(url_for('.show_categories'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'edit'
    form.name.data = category.name
    form.pid.data = category.pid
    form.sort_order.data = category.sort_order
    form.description.data = category.description
    form.status.data = category.status

    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())

    return render_template('categories/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='categories',
                           category=category,
                           paginated_categories=paginated_categories,
                           **load_common_data())


@main.route('/categories/delete', methods=['POST'])
@login_required
@user_has('admin_product')
def delete_category():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete category is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            category = Category.query.get_or_404(int(id))
            db.session.delete(category)
        db.session.commit()

        flash('Delete category is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete category is fail!', 'danger')

    return redirect(url_for('.show_categories'))


@main.route('/suppliers/search_supply', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def search_supply():
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    sk = request.values.get('sk', type=str, default='ad')

    builder = SupplyStats.query.filter_by(master_uid=Master.master_uid())
    qk = qk.strip()
    if qk:
        builder = builder.whoosh_search(qk, like=True)

    supply = builder.order_by('%s desc' % SORT_TYPE_CODE[sk]).all()

    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))

    paginated_supply = supply[start:end]

    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    return render_template('suppliers/search_supply.html',
                           qk=qk,
                           sk=sk,
                           paginated_supply=paginated_supply,
                           pagination=pagination)


@main.route('/suppliers/supply_list', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def supply_list():
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    paginated_supply = SupplyStats.query.filter_by(master_uid=Master.master_uid()).order_by(SupplyStats.created_at.desc()).paginate(
        page, per_page)
    return render_template('suppliers/supply_list.html',
                           sub_menu='supply',
                           paginated_supply=paginated_supply.items,
                           pagination=paginated_supply,
                           **load_common_data())


def get_order_key(key):
    switch_dict = {
        'ad': Supplier.created_at.desc,
        'ud': Supplier.updated_at.desc,
        'ed': Supplier.end_date.desc
    }
    return switch_dict.get(key)() if switch_dict.get(key) else Supplier.created_at.desc()


@main.route('/suppliers/search', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def search_suppliers():
    """搜索供应商"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    sk = request.values.get('sk', type=str, default='ad')

    current_app.logger.debug('qk[%s], sk[%s]' % (qk, sk))

    builder = Supplier.query.filter_by(master_uid=Master.master_uid())
    qk = qk.strip()
    if qk:
        builder = builder.whoosh_search(qk, like=True)

    suppliers = builder.order_by(get_order_key(sk)).all()

    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))

    paginated_suppliers = suppliers[start:end]

    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    return render_template('suppliers/search_result.html',
                           qk=qk,
                           sk=sk,
                           paginated_suppliers=paginated_suppliers,
                           pagination=pagination)


@main.route('/suppliers', methods=['GET', 'POST'])
@main.route('/suppliers/<int:page>', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def show_suppliers(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by(Supplier.created_at.desc()).paginate(page, per_page)
    return render_template('suppliers/show_list.html',
                           sub_menu='suppliers',
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/suppliers/create', methods=['GET', 'POST'])
@login_required
@user_has('admin_supplier')
def create_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            master_uid=Master.master_uid(),
            type=form.type.data,
            short_name=form.short_name.data,
            full_name=form.full_name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            contact_name=form.contact_name.data,
            phone=form.phone.data,
            address=form.address.data,
            remark=form.remark.data
        )
        db.session.add(supplier)
        db.session.commit()

        flash('Add supplier is ok!', 'success')

        return redirect(url_for('.show_suppliers'))

    mode = 'create'
    return render_template('suppliers/create_and_edit.html',
                           form=form,
                           mode=mode,
                           supplier=None,
                           sub_menu='suppliers',
                           **load_common_data())


@main.route('/suppliers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_supplier')
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    form = SupplierForm()
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()

        flash('Edit supplier is ok!', 'success')

        return redirect(url_for('.show_suppliers'))

    mode = 'edit'
    form.type.data = supplier.type
    form.short_name.data = supplier.short_name
    form.full_name.data = supplier.full_name
    form.start_date.data = supplier.start_date
    form.end_date.data = supplier.end_date
    form.contact_name.data = supplier.contact_name
    form.phone.data = supplier.phone
    form.address.data = supplier.address
    form.remark.data = supplier.remark
    return render_template('suppliers/create_and_edit.html',
                           form=form,
                           mode=mode,
                           supplier=supplier,
                           sub_menu='suppliers',
                           **load_common_data())


@main.route('/suppliers/delete', methods=['POST'])
@login_required
@user_has('admin_supplier')
def delete_supplier():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete supplier is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            supplier = Supplier.query.get_or_404(int(id))
            db.session.delete(supplier)
        db.session.commit()

        flash('Delete supplier is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete supplier is fail!', 'danger')

    return redirect(url_for('.show_suppliers'))



