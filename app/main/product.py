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
from app.models import Product, Supplier, Category, ProductSku, ProductStock, WarehouseShelve, Asset, SupplyStats,\
    Currency, Order, OrderItem
from app.forms import ProductForm, SupplierForm, CategoryForm, EditCategoryForm, ProductSkuForm
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

@main.route('/products')
@main.route('/products/<int:page>')
@login_required
@user_has('admin_product')
def show_products(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    builder = Product.query.filter_by(master_uid=Master.master_uid())

    paginated_result = builder.order_by('created_at desc').paginate(page, per_page)
    
    # 品牌列表
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(
        1, 1000)
    
    return render_template('products/show_list.html',
                           sub_menu='products',
                           paginated_products=paginated_result.items,
                           pagination=paginated_result,
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/products/search', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def search_products():
    """支持全文索引搜索产品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    reg_id = request.values.get('reg_id', type=int)
    bra_id = request.values.get('bra_id', type=int)
    sk = request.values.get('sk', type=str, default='ad')

    current_app.logger.debug('qk[%s], sk[%s]' % (qk, sk))

    builder = Product.query.filter_by(master_uid=Master.master_uid())
    if reg_id:
        builder = builder.filter_by(region_id=reg_id)
    if bra_id:
        builder = builder.filter_by(supplier_id=bra_id)

    qk = qk.strip()
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
                           reg_id=reg_id,
                           bra_id=bra_id,
                           paginated_products=paginated_products,
                           pagination=pagination)


@main.route('/products/ajax_search', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def ajax_search_products():
    """搜索产品,满足采购等选择产品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    supplier_id = request.values.get('supplier_id', type=int)
    qk = request.values.get('qk')
    reg_id = request.values.get('reg_id', type=int)
    
    if request.method == 'POST':
        builder = ProductSku.query.filter_by(master_uid=Master.master_uid(), supplier_id=supplier_id)
        if reg_id:
            builder = builder.filter_by(region_id=reg_id)
        
        qk = qk.strip()
        if qk:
            builder = builder.whoosh_search(qk, like=True)

        skus = builder.order_by(ProductSku.created_at.desc()).all()

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
                               pagination=pagination,
                               supplier_id=supplier_id,
                               reg_id=reg_id,
                               qk=qk)

    paginated_skus = ProductSku.query.filter_by(master_uid=Master.master_uid(), supplier_id=supplier_id).order_by(ProductSku.created_at.desc()).paginate(page, per_page)
    
    return render_template('purchases/purchase_modal.html',
                           supplier_id=supplier_id,
                           default_regions=DEFAULT_REGIONS,
                           paginated_skus=paginated_skus)


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


@main.route('/products/ajax_select', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def ajax_select_products():
    """搜索库存产品,满足下单/出库等选择产品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    wh_id = request.values.get('wh_id')
    qk = request.values.get('qk')
    t = request.values.get('t')
    
    builder = ProductStock.query.filter_by(master_uid=Master.master_uid())
    if wh_id:
        builder = builder.filter_by(warehouse_id=wh_id)
        
    if qk:
        qk = qk.strip()
        builder = builder.filter_by(sku_serial_no=qk)

    paginated_stocks = builder.order_by('created_at desc').paginate(page, per_page)
    
        
    return render_template('products/select_product_modal.html',
                           paginated_stocks=paginated_stocks,
                           wh_id=wh_id,
                           qk=qk,
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
    currency_list = Currency.query.filter_by(status=1).all()

    form = ProductForm()
    form.currency_id.choices = [(currency.id, '%s - %s' % (currency.title, currency.code)) for currency in currency_list]
    if form.validate_on_submit():
        next_action = request.form.get('next_action', 'finish_save')
        # 设置默认值
        if not form.cover_id.data:
            default_cover = Asset.query.filter_by(is_default=True).first()
            form.cover_id.data = default_cover.id

        new_serial_no = form.serial_no.data
        current_app.logger.warn('Product new serial_no [%s] -----!!!' % new_serial_no)

        product = Product(
            master_uid=Master.master_uid(),
            serial_no=new_serial_no,
            supplier_id=form.supplier_id.data,
            name=form.name.data,
            cover_id=form.cover_id.data,
            currency_id=form.currency_id.data,
            region_id=form.region_id.data,
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
        
        # 新增索引
        flask_whooshalchemyplus.index_one_model(Product)

        db.session.commit()

        if next_action == 'continue_save':
            flash(gettext('The basic information is complete and continue editing'), 'success')
            return redirect(url_for('.edit_product', rid=product.serial_no))

        flash(gettext('The basic information is complete'), 'success')
        return redirect(url_for('.show_products'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'create'
    form.serial_no.data = Product.make_unique_serial_no(gen_serial_no())
    # 默认为官网默认货币
    form.currency_id.data = g.current_site.currency_id

    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(1, 1000)

    return render_template('products/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='products',
                           current_currency_unit=g.current_site.currency,
                           product=None,
                           paginated_categories=paginated_categories,
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/products/<string:rid>/edit', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def edit_product(rid):
    product = Product.query.filter_by(serial_no=rid).first()
    if product is None:
        abort(404)

    currency_list = Currency.query.filter_by(status=1).all()
    form = ProductForm()
    form.currency_id.choices = [(currency.id, '%s - %s' % (currency.title, currency.code)) for currency in
                                currency_list]
    if form.validate_on_submit():
        form.populate_obj(product)

        # 更新所属分类
        if form.category_id.data:
            categories = []
            categories.append(Category.query.get(form.category_id.data))

            product.update_categories(*categories)

        db.session.commit()

        next_action = request.form.get('next_action', 'finish_save')
        if next_action == 'continue_save':
            flash(gettext('Basic information is complete and continue editing'), 'success')
            return redirect(url_for('.edit_product', rid=product.serial_no))

        flash(gettext('Basic information is complete'), 'success')
        return redirect(url_for('.show_products'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'edit'

    form.serial_no.data = product.serial_no
    form.supplier_id.data = product.supplier_id
    form.name.data = product.name
    form.cover_id.data = product.cover_id
    # 默认为官网默认货币
    form.currency_id.data = product.currency_id if product.currency_id else g.current_site.currency_id
    form.region_id.data = product.region_id
    form.cost_price.data = product.cost_price
    form.sale_price.data = product.sale_price
    form.s_weight.data = product.s_weight
    form.s_length.data = product.s_length
    form.s_width.data = product.s_width
    form.s_height.data = product.s_height
    form.from_url.data = product.from_url
    form.status.data = product.status
    form.description.data = product.description

    # 当前货币类型
    if product.currency_id:
        current_currency = Currency.query.get(product.currency_id)
        current_currency_unit = current_currency.code
    else:
        current_currency_unit = g.current_site.currency

    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(1, 1000)

    return render_template('products/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='products',
                           product=product,
                           current_currency_unit=current_currency_unit,
                           paginated_categories=paginated_categories,
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/products/delete', methods=['POST'])
@login_required
@user_has('admin_product')
def delete_product():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash(gettext('Delete product is null!'), 'danger')
        abort(404)

    try:
        for rid in selected_ids:
            product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first()
            if product:
                db.session.delete(product)

        db.session.commit()

    except Exception as ex:
        current_app.logger.debug('Delete product is fail: %s' % ex)

    flash(gettext('Delete product is ok!'), 'success')

    return redirect(url_for('.show_products'))


@main.route('/products/copy')
@login_required
@user_has('admin_product')
def copy_product():
    """复制产品"""
    rid = request.values.get('rid')
    if rid is None:
        abort(404)

    new_region_id = request.values.get('reg_id', 0, type=int)

    product = Product.query.filter_by(serial_no=rid).first()
    if product is None:
        abort(404)

    if product.region_id == new_region_id:
        flash(gettext('Product already exists without duplication'), 'danger')
        return redirect(url_for('.show_products'))

    currency_list = Currency.query.filter_by(status=1).all()
    new_serial_no = Product.make_unique_serial_no(gen_serial_no())
    copy_product = Product(
        master_uid=Master.master_uid(),
        serial_no=new_serial_no,
        supplier_id=product.supplier_id,
        name=product.name,
        cover_id=product.cover_id,
        currency_id=product.currency_id,
        region_id=new_region_id,
        cost_price=product.cost_price,
        sale_price=product.sale_price,
        s_weight=product.s_weight,
        s_length=product.s_length,
        s_width=product.s_width,
        s_height=product.s_height,
        from_url=product.from_url,
        status=product.status,
        description=product.description
    )
    db.session.add(copy_product)

    # 更新所属分类
    if product.categories:
        categories = product.categories
        copy_product.update_categories(*categories)

    # 复制SKU
    for sku in product.skus:
        copy_sku = ProductSku(
            product_id=copy_product.id,
            supplier_id=copy_product.supplier_id,
            master_uid=Master.master_uid(),
            serial_no=ProductSku.make_unique_serial_no(gen_serial_no()),
            cover_id=sku.cover_id,
            id_code=sku.id_code,
            s_model=sku.s_model,
            s_color=sku.s_color,
            s_weight=sku.s_weight,
            cost_price=sku.cost_price,
            sale_price=sku.sale_price,
            remark=sku.remark
        )
        db.session.add(copy_sku)

    db.session.commit()

    flash(gettext('Copy product is ok!'), 'success')

    return redirect(url_for('main.edit_product', rid=copy_product.serial_no))


@main.route('/products/import', methods=['GET', 'POST'])
@login_required
@user_has('admin_product')
def import_product():
    if request.method == 'POST' and 'excel' in request.files:
        reg_id = request.form.get('reg_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int)

        sub_folder = str(time.strftime('%y%m%d'))
        for f in request.files.getlist('excel'):
            # start to save
            name_prefix = 'admin' + str(time.time())
            name_prefix = hashlib.md5(name_prefix.encode('utf-8')).hexdigest()[:15]
            filename = uploader.save(f, folder=sub_folder, name=name_prefix + '.')

            storage_filepath = uploader.path(filename)
            current_app.logger.debug('Excel file [%s]' % storage_filepath)

            # 读取文档内容
            products = import_product_from_excel(storage_filepath)

            # 默认封面图
            default_cover = Asset.query.filter_by(is_default=True).first()

            for product_dict in products:
                id_code = product_dict.get('id_code')
                # 69码不存在，跳过
                if id_code is None or re.match(r'^\d{13}$', id_code) is None:
                    continue

                # 验证sku是否已存在
                rows = ProductSku.validate_unique_id_code(id_code, region_id=reg_id, master_uid=Master.master_uid())
                if len(rows) >= 1:
                    # 已存在，则跳过
                    continue

                current_app.logger.debug('current product [%s]' % product_dict)

                sku_dict = {
                    'supplier_id' : supplier_id,
                    'master_uid' : Master.master_uid(),
                    'serial_no' : ProductSku.make_unique_serial_no(gen_serial_no()),
                    'id_code' : id_code,
                    'cover_id' : default_cover.id,
                    's_model' : product_dict.get('mode'),
                    's_color' : product_dict.get('color'),
                    'cost_price' : product_dict.get('cost_price')
                }
                current_app.logger.debug('current product sku [%s]' % sku_dict)

                # 验证产品是否存在
                if product_dict.get('first_id_code'):
                    first_sku = ProductSku.query.filter_by(master_uid=Master.master_uid(), id_code=product_dict.get('first_id_code')).first()
                    sku_dict['product_id'] = first_sku.product_id

                    # 同步添加sku
                    new_sku = ProductSku(**sku_dict)
                    db.session.add(new_sku)
                else:
                    # 新增产品
                    product_dict['reg_id'] = reg_id
                    product_dict['supplier_id'] = supplier_id
                    product_dict['currency_id'] = g.current_site.currency_id
                    product_dict['cover_id'] = default_cover.id
                    product_dict['serial_no'] = Product.make_unique_serial_no(gen_serial_no())
                    product_dict['status'] = True
                    new_product = Product.from_json(product_dict, master_uid=Master.master_uid())
                    db.session.add(new_product)

                    # 同步添加sku
                    new_sku = ProductSku(product=new_product, **sku_dict)
                    db.session.add(new_sku)

            db.session.commit()

        flash(gettext('Import product is ok!'), 'success')

        return redirect(url_for('.show_products'))

    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(
        1, 1000)
    return render_template('products/_modal_import.html',
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/products/download_template')
@login_required
@user_has('admin_product')
def download_product_tpl():
    pass


@main.route('/products/<string:rid>/skus')
@user_has('admin_product')
def show_skus(rid):
    product = Product.query.filter_by(serial_no=rid).first()
    if product is None:
        abort(404)

    return render_template('products/show_skus.html',
                           product_skus=product.skus,
                           product=product)

@main.route('/products/<string:rid>/add_sku', methods=['GET', 'POST'])
@user_has('admin_product')
def add_sku(rid):
    product = Product.query.filter_by(serial_no=rid).first()
    if product is None:
        abort(404)

    form = ProductSkuForm()
    if form.validate_on_submit():
        # 设置默认值
        if not form.sku_cover_id.data:
            default_cover = Asset.query.filter_by(is_default=True).first()
            form.sku_cover_id.data = default_cover.id

        new_serial_no = form.serial_no.data
        current_app.logger.warn('Sku new serial_no [%s] -----!!!' % new_serial_no)

        # 验证69码是否重复
        id_code = form.id_code.data

        #rows = ProductSku.validate_unique_id_code(id_code=id_code, region_id=product.region_id)
        #if len(rows) >= 1:
        #    return custom_response(False, gettext('Commodity Codes [%s] already exist!' % id_code))

        sku = ProductSku(
            product_id=product.id,
            supplier_id=product.supplier_id,
            master_uid=Master.master_uid(),
            serial_no=new_serial_no,
            id_code=id_code,
            cover_id=form.sku_cover_id.data,
            s_model=form.s_model.data,
            s_color=form.s_color.data,
            s_weight=form.s_weight.data,
            cost_price=form.cost_price.data,
            sale_price=form.sale_price.data,
            region_id=product.region_id,
            remark=form.remark.data
        )
        db.session.add(sku)

        # 新增索引
        flask_whooshalchemyplus.index_one_model(Product)
        flask_whooshalchemyplus.index_one_model(ProductSku)
        
        db.session.commit()

        return full_response(True, R201_CREATED, sku.to_json())

    mode = 'create'
    form.serial_no.data = ProductSku.make_unique_serial_no(gen_serial_no())
    form.cost_price.data = product.cost_price
    form.sale_price.data = product.sale_price
    form.s_weight.data = product.s_weight
    return render_template('products/modal_sku.html',
                           form=form,
                           mode=mode,
                           post_sku_url=url_for('.add_sku', rid=rid),
                           product=product)


@main.route('/products/<string:rid>/edit_sku/<int:s_id>', methods=['GET', 'POST'])
@user_has('admin_product')
def edit_sku(rid, s_id):
    product = Product.query.filter_by(serial_no=rid).first()
    if product is None:
        abort(404)

    sku = ProductSku.query.get_or_404(s_id)
    form = ProductSkuForm()
    if form.validate_on_submit():
        # 验证69码是否重复
        id_code = form.id_code.data
        
        #rows = ProductSku.validate_unique_id_code(id_code=id_code, region_id=product.region_id)
        #if len(rows) > 1 or (len(rows) == 1 and rows[0][0] != s_id):
        #    return custom_response(False, gettext('Commodity Codes [%s] already exist!' % id_code))

        sku.cover_id = form.sku_cover_id.data
        sku.id_code = form.id_code.data
        sku.s_model = form.s_model.data
        sku.s_color = form.s_color.data
        sku.s_weight = form.s_weight.data
        sku.cost_price = form.cost_price.data
        sku.sale_price = form.sale_price.data
        sku.region_id = product.region_id
        sku.remark = form.remark.data

        db.session.commit()

        return full_response(True, R201_CREATED, sku.to_json())

    mode = 'edit'

    form.serial_no.data = sku.serial_no
    form.sku_cover_id.data = sku.cover_id
    form.id_code.data = sku.id_code
    form.cost_price.data = sku.cost_price
    form.sale_price.data = sku.sale_price
    form.s_model.data = sku.s_model
    form.s_color.data = sku.s_color
    form.s_weight.data = sku.s_weight
    form.remark.data = sku.remark

    return render_template('products/modal_sku.html',
                           form=form,
                           mode=mode,
                           product=product,
                           post_sku_url=url_for('.edit_sku', rid=rid, s_id=s_id),
                           sku=sku)


@main.route('/products/<string:rid>/delete_sku', methods=['POST'])
@user_has('admin_product')
def delete_sku(rid):
    try:
        sku = ProductSku.query.filter_by(serial_no=rid).first()
        if sku is None:
            return custom_response(False, gettext("Product Sku isn't exist!"))

        db.session.delete(sku)
        db.session.commit()

        return full_response(True, R204_NOCONTENT, {'id': rid})
    except:
        db.session.rollback()
        return full_response(True, custom_status('Delete sku is failed!', 500))


@main.route('/products/<string:rid>/orders')
@login_required
def sku_of_orders(rid):
    """某个sku订单列表"""
    per_page = request.args.get('per_page', 15, type=int)
    page = request.args.get('page', 1, type=int)
    
    builder = OrderItem.query.filter_by(sku_serial_no=rid)
    builder = builder.join(Order, OrderItem.order_id==Order.id).filter(Order.master_uid==Master.master_uid())
    
    paginated_orders = builder.order_by(OrderItem.id.desc()).paginate(page, per_page)

    # 当前销售总数
    total_quantity = builder.with_entities(func.sum(OrderItem.quantity)).one()
    
    # 销售总金额
    total_sales = builder.with_entities(func.sum(OrderItem.quantity * OrderItem.deal_price), func.sum(OrderItem.discount_amount)).one()

    total_amount = 0
    if total_sales and total_sales[0]:
        total_amount = total_sales[0] - total_sales[1]
        
    
    return render_template('products/sku_of_orders.html',
                           paginated_orders=paginated_orders,
                           total_amount=total_amount,
                           total_quantity=total_quantity)


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


@main.route('/categories/repair')
@main.route('/categories/repair/<int:parent_id>')
@login_required
def repair_category_path(parent_id=0):

    Category.repair_categories(Master.master_uid(), parent_id)

    return redirect(url_for('.show_categories'))


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
        Category.repair_categories(Master.master_uid(), category.pid)

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
        Category.repair_categories(Master.master_uid(), category.pid)

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

            # rebuild category path
            Category.repair_categories(Master.master_uid(), id)

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



