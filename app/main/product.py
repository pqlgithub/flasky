# -*- coding: utf-8 -*-
import time, hashlib, re
from flask import g, render_template, redirect, url_for, abort, flash, request, current_app
from flask_sqlalchemy import Pagination
from sqlalchemy.sql import func
from flask_babelex import gettext
import flask_whooshalchemyplus

from . import main
from .. import db, uploader
from app.models import Product, Supplier, Category, ProductSku, ProductContent, ProductStock, WarehouseShelve, Asset, \
    SupplyStats, Order, OrderItem, Brand, ProductPacket, WxMiniApp, WxAuthorizer, DiscountTempletItem, DiscountTemplet
from app.forms import ProductForm, SupplierForm, CategoryForm, EditCategoryForm, ProductSkuForm, ProductGroupForm, \
    DiscountTempletForm, DiscountTempletEditForm
from ..utils import Master, full_response, status_response, custom_status, R200_OK, R201_CREATED, R204_NOCONTENT,\
    custom_response, import_product_from_excel, form_errors_list, form_errors_response, flash_errors, gen_serial_no
from ..decorators import user_has
from ..constant import SORT_TYPE_CODE, DEFAULT_REGIONS
from app.helpers import QiniuStorage, WxaOpen3rd, WxAppError, Fxaim
from qiniu import Auth, put_data


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
@user_has('admin_product')
def show_products(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    builder = Product.query.filter_by(master_uid=Master.master_uid())

    paginated_result = builder.order_by('created_at desc').paginate(page, per_page)
    
    # 品牌列表
    paginated_brands = Brand.query.filter_by(master_uid=Master.master_uid()).order_by(Brand.created_at.asc()).paginate(
        1, 1000)
    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    return render_template('products/show_list.html',
                           sub_menu='products',
                           paginated_products=paginated_result.items,
                           pagination=paginated_result,
                           paginated_brands=paginated_brands,
                           paginated_categories=paginated_categories,
                           **load_common_data())


@main.route('/products/search', methods=['GET', 'POST'])
@user_has('admin_product')
def search_products():
    """支持全文索引搜索产品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    qk = request.values.get('qk')
    cate_id = request.values.get('cate_id', type=int)
    bra_id = request.values.get('bra_id', type=int)
    sk = request.values.get('sk', type=str, default='ad')

    current_app.logger.debug('qk[%s], sk[%s]' % (qk, sk))

    if cate_id:
        category = Category.query.get(cate_id)
        builder = category.products.filter_by(master_uid=Master.master_uid())
    else:
        builder = Product.query.filter_by(master_uid=Master.master_uid())

    if bra_id:
        builder = builder.filter_by(brand_id=bra_id)
    
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
                           cate_id=cate_id,
                           bra_id=bra_id,
                           paginated_products=paginated_products,
                           pagination=pagination)


@main.route('/products/ajax_search', methods=['GET', 'POST'])
@user_has('admin_product')
def ajax_search_products():
    """搜索产品,满足采购等选择产品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    supplier_id = request.values.get('supplier_id', type=int)
    reg_id = request.values.get('reg_id', type=int)
    qk = request.values.get('qk')
    selected_ids = request.values.getlist('selected[]')

    builder = ProductSku.query.filter_by(master_uid=Master.master_uid(), supplier_id=supplier_id)
    if reg_id:
        builder = builder.filter_by(region_id=reg_id)

    if qk:
        qk = qk.strip()
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
    
    # 获取已经选中的sku
    selected_skus = None
    if selected_ids is not None:
        selected_ids = [int(sku_id) for sku_id in selected_ids]
        selected_skus = ProductSku.query.filter_by(master_uid=Master.master_uid()).filter(ProductSku.id.in_(selected_ids)).all()
    
    current_tpl = 'purchases/purchase_modal.html'
    if request.method == 'POST':
        current_tpl = 'purchases/purchase_tr_time.html'
    
    return render_template(current_tpl,
                           default_regions=DEFAULT_REGIONS,
                           paginated_skus=paginated_skus,
                           pagination=pagination,
                           supplier_id=supplier_id,
                           reg_id=reg_id,
                           qk=qk,
                           selected_ids=selected_ids,
                           selected_skus=selected_skus)
    

@main.route('/products/skus', methods=['POST'])
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
@user_has('admin_product')
def create_product():
    form = ProductForm()
    if form.validate_on_submit():
        next_action = request.form.get('next_action', 'finish_save')
        # 设置默认值
        if not form.cover_id.data:
            default_cover = Asset.query.filter_by(is_default=True).first()
            form.cover_id.data = default_cover.id

        new_serial_no = form.serial_no.data
        current_app.logger.warn('Product new serial_no [%s] -----!!!' % new_serial_no)
        
        # 根据品牌获取供应商
        if form.brand_id.data:
            brand = Brand.query.filter_by(master_uid=Master.master_uid(), id=form.brand_id.data).first()
            form.supplier_id.data = brand.supplier_id if brand else 0

        product = Product(
            master_uid=Master.master_uid(),
            serial_no=new_serial_no,
            supplier_id=form.supplier_id.data,
            brand_id=form.brand_id.data,
            name=form.name.data,
            cover_id=form.cover_id.data,
            region_id=form.region_id.data,
            cost_price=form.cost_price.data,
            price=form.price.data,
            sale_price=form.sale_price.data,
            s_weight=form.s_weight.data,
            s_length=form.s_length.data,
            s_width=form.s_width.data,
            s_height=form.s_height.data,
            from_url=form.from_url.data,
            status=form.status.data,
            sticked=form.sticked.data,
            features=form.features.data,
            description=form.description.data
        )

        db.session.add(product)
        
        # 更新内容详情
        asset_ids = request.form.getlist('asset_ids[]')
        if form.tags.data or form.content.data or asset_ids:
            detail = ProductContent(
                master_uid=Master.master_uid(),
                asset_ids=','.join(asset_ids),
                tags=form.tags.data,
                content=form.content.data
            )
            detail.product = product
            db.session.add(detail)

        # 更新所属分类
        if form.category_id.data:
            categories = []
            categories.append(Category.query.get(form.category_id.data))
            product.update_categories(*categories)
        
        db.session.commit()

        # 新增索引
        # flask_whooshalchemyplus.index_one_model(Product)

        if next_action == 'continue_save':
            flash(gettext('The basic information is complete and continue editing'), 'success')
            return redirect(url_for('.edit_product', rid=product.serial_no))

        flash(gettext('The basic information is complete'), 'success')
        
        return redirect(url_for('.show_products'))
    else:
        current_app.logger.debug(form.errors)

    mode = 'create'
    # 初始化编号
    form.serial_no.data = Product.make_unique_serial_no(gen_serial_no())

    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    paginated_brands = Brand.query.filter_by(master_uid=Master.master_uid())\
        .order_by(Brand.created_at.desc()).paginate(1, 1000)

    # 生成上传token
    cfg = current_app.config
    up_token = QiniuStorage.up_token(cfg['QINIU_ACCESS_KEY'], cfg['QINIU_ACCESS_SECRET'], cfg['QINIU_BUCKET_NAME'],
                                     cfg['DOMAIN_URL'])
    if current_app.config['MODE'] == 'prod':
        up_endpoint = cfg['QINIU_UPLOAD']
    else:
        up_endpoint = url_for('main.flupload')

    return render_template('products/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='products',
                           up_endpoint=up_endpoint,
                           up_token=up_token,
                           current_currency_unit=g.current_site.currency,
                           product=None,
                           paginated_categories=paginated_categories,
                           paginated_brands=paginated_brands,
                           **load_common_data())


@main.route('/products/<string:rid>/edit', methods=['GET', 'POST'])
@user_has('admin_product')
def edit_product(rid):
    product = Product.query.filter_by(serial_no=rid).first()
    if product is None:
        abort(404)

    form = ProductForm()
    if form.validate_on_submit():
        # 根据品牌获取供应商
        if form.brand_id.data:
            brand = Brand.query.filter_by(master_uid=Master.master_uid(), id=form.brand_id.data).first()
            form.supplier_id.data = brand.supplier_id if brand else 0
        
        form.populate_obj(product)

        # 同步sku销售价及促销价
        price = form.price.data if form.price.data else 0.0
        sale_price = form.sale_price.data if form.sale_price.data else 0.0
        for sku in product.skus:
            sku.price = price
            sku.sale_price = sale_price

        # 更新内容详情
        asset_ids = request.form.getlist('asset_ids[]')
        if form.tags.data or form.content.data or asset_ids:
            if product.details:  # 已存在，则更新
                product.details.asset_ids = ','.join(asset_ids)
                product.details.tags = form.tags.data
                product.details.content = form.content.data
            else:
                detail = ProductContent(
                    master_uid=Master.master_uid(),
                    asset_ids=','.join(asset_ids),
                    tags=form.tags.data,
                    content=form.content.data
                )
                detail.product = product
                db.session.add(detail)
        
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
    form.brand_id.data = product.brand_id
    form.name.data = product.name
    form.cover_id.data = product.cover_id
    form.region_id.data = product.region_id
    form.cost_price.data = product.cost_price
    form.price.data = product.price
    form.sale_price.data = product.sale_price
    form.s_weight.data = product.s_weight
    form.s_length.data = product.s_length
    form.s_width.data = product.s_width
    form.s_height.data = product.s_height
    form.from_url.data = product.from_url
    form.status.data = product.status
    form.sticked.data = product.sticked
    form.features.data = product.features
    form.description.data = product.description
    # 内容详情
    if product.details:
        form.tags.data = product.details.tags
        form.content.data = product.details.content
    
    # 当前货币类型
    current_currency_unit = g.current_site.currency

    paginated_categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    paginated_brands = Brand.query.filter_by(master_uid=Master.master_uid()).order_by('created_at desc').paginate(1,
                                                                                                                  1000)
    # 生成上传token
    cfg = current_app.config
    up_token = QiniuStorage.up_token(cfg['QINIU_ACCESS_KEY'], cfg['QINIU_ACCESS_SECRET'], cfg['QINIU_BUCKET_NAME'],
                                     cfg['DOMAIN_URL'])
    if current_app.config['MODE'] == 'prod':
        up_endpoint = cfg['QINIU_UPLOAD']
    else:
        up_endpoint = url_for('main.flupload')

    return render_template('products/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='products',
                           product=product,
                           up_endpoint=up_endpoint,
                           up_token=up_token,
                           current_currency_unit=current_currency_unit,
                           paginated_categories=paginated_categories,
                           paginated_brands=paginated_brands,
                           **load_common_data())


@main.route('/products/delete', methods=['POST'])
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

    new_serial_no = Product.make_unique_serial_no(gen_serial_no())
    some_product = Product(
        master_uid=Master.master_uid(),
        serial_no=new_serial_no,
        supplier_id=product.supplier_id,
        name=product.name,
        cover_id=product.cover_id,
        currency_id=product.currency_id,
        region_id=new_region_id,
        cost_price=product.cost_price,
        price=product.price,
        sale_price=product.sale_price,
        s_weight=product.s_weight,
        s_length=product.s_length,
        s_width=product.s_width,
        s_height=product.s_height,
        from_url=product.from_url,
        status=product.status,
        description=product.description
    )
    db.session.add(some_product)

    # 更新所属分类
    if product.categories:
        categories = product.categories
        some_product.update_categories(*categories)

    # 复制SKU
    for sku in product.skus:
        copy_sku = ProductSku(
            product_id=some_product.id,
            supplier_id=some_product.supplier_id,
            master_uid=Master.master_uid(),
            serial_no=ProductSku.make_unique_serial_no(gen_serial_no()),
            cover_id=sku.cover_id,
            id_code=sku.id_code,
            s_model=sku.s_model,
            s_color=sku.s_color,
            s_weight=sku.s_weight,
            cost_price=sku.cost_price,
            price=sku.price,
            sale_price=sku.sale_price,
            remark=sku.remark
        )
        db.session.add(copy_sku)

    db.session.commit()

    flash(gettext('Copy product is ok!'), 'success')

    return redirect(url_for('main.edit_product', rid=some_product.serial_no))


@main.route('/products/import', methods=['GET', 'POST'])
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
                rows = ProductSku.validate_unique_id_code(id_code, master_uid=Master.master_uid())
                if len(rows) >= 1:
                    # 已存在，则跳过
                    continue

                current_app.logger.debug('current product [%s]' % product_dict)

                sku_dict = {
                    'supplier_id': supplier_id,
                    'master_uid': Master.master_uid(),
                    'serial_no': ProductSku.make_unique_serial_no(gen_serial_no()),
                    'id_code': id_code,
                    'cover_id': default_cover.id,
                    's_model': product_dict.get('mode'),
                    's_color': product_dict.get('color'),
                    'cost_price': product_dict.get('cost_price')
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
@user_has('admin_product')
def download_product_tpl():
    pass


@main.route('/products/<string:rid>/skus')
@user_has('admin_product')
def show_skus(rid):
    product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first()
    if product is None:
        abort(404)

    return render_template('products/show_skus.html',
                           product_skus=product.skus,
                           product=product)


@main.route('/products/<string:rid>/add_sku', methods=['GET', 'POST'])
@user_has('admin_product')
def add_sku(rid):
    product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first()
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
            price=form.price.data,
            sale_price=form.sale_price.data,
            region_id=product.region_id,
            stock_quantity=form.stock_quantity.data,
            remark=form.remark.data
        )
        db.session.add(sku)
        
        db.session.commit()

        # run the task
        _dispatch_sku_task(sku.master_uid, sku.product_id, sku.supplier_id)

        tr_html = render_template('products/_tr_sku.html',
                                  product=product,
                                  sku=sku)

        return full_response(True, R201_CREATED, {
            'tr_html': tr_html
        })

    mode = 'create'
    form.serial_no.data = ProductSku.make_unique_serial_no(gen_serial_no())
    form.cost_price.data = product.cost_price
    form.price.data = product.price
    form.sale_price.data = product.sale_price
    form.s_weight.data = product.s_weight
    return render_template('products/modal_sku.html',
                           form=form,
                           mode=mode,
                           product=product,
                           post_sku_url=url_for('.add_sku', rid=rid),
                           # 当前货币类型
                           current_currency_unit=g.current_site.currency)


@main.route('/products/<string:rid>/edit_sku/<int:s_id>', methods=['GET', 'POST'])
@user_has('admin_product')
def edit_sku(rid, s_id):
    product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first()
    if product is None:
        abort(404)

    sku = ProductSku.query.get_or_404(s_id)
    form = ProductSkuForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            error_list = form_errors_list(form)
            return form_errors_response(error_list)

        # 验证69码是否重复
        id_code = form.id_code.data

        sku.cover_id = form.sku_cover_id.data
        sku.id_code = form.id_code.data
        sku.s_model = form.s_model.data
        sku.s_color = form.s_color.data
        sku.s_weight = form.s_weight.data
        sku.id_code = id_code
        sku.cost_price = form.cost_price.data
        sku.price = form.price.data
        sku.sale_price = form.sale_price.data
        sku.stock_quantity = form.stock_quantity.data
        sku.remark = form.remark.data
        sku.region_id = product.region_id

        db.session.commit()

        # run the task
        current_app.logger.warn('uid: %d, pid: %d, spid: %d' % (sku.master_uid, sku.product_id, sku.supplier_id))

        _dispatch_sku_task(sku.master_uid, sku.product_id, sku.supplier_id)

        return full_response(True, R201_CREATED, sku.to_json())

    mode = 'edit'

    form.serial_no.data = sku.serial_no
    form.sku_cover_id.data = sku.cover_id
    form.id_code.data = sku.id_code
    form.cost_price.data = sku.cost_price
    form.price.data = sku.price
    form.sale_price.data = sku.sale_price
    form.s_model.data = sku.s_model
    form.s_color.data = sku.s_color
    form.s_weight.data = sku.s_weight
    form.stock_quantity.data = sku.stock_quantity
    form.remark.data = sku.remark

    return render_template('products/modal_sku.html',
                           form=form,
                           mode=mode,
                           product=product,
                           post_sku_url=url_for('.edit_sku', rid=rid, s_id=s_id),
                           sku=sku,
                           # 当前货币类型
                           current_currency_unit=g.current_site.currency)


@main.route('/products/<string:rid>/delete_sku', methods=['POST'])
@user_has('admin_product')
def delete_sku(rid):
    try:
        sku = ProductSku.query.filter_by(serial_no=rid).first()
        if sku is None:
            return custom_response(False, gettext("Product Sku isn't exist!"))

        product_id = sku.product_id
        master_uid = sku.master_uid
        supplier_id = sku.supplier_id

        db.session.delete(sku)

        db.session.commit()

        # run the task
        _dispatch_sku_task(master_uid, product_id, supplier_id)

        return full_response(True, R204_NOCONTENT, {'id': rid})

    except Exception as err:
        db.session.rollback()
        return full_response(True, custom_status('Delete sku is failed!', 500))


def _dispatch_sku_task(master_uid, product_id, supplier_id):
    from app.tasks import sync_supply_stats, sync_product_stock

    sync_product_stock.apply_async(args=[product_id], countdown=5)
    if supplier_id:
        sync_supply_stats.apply_async(args=[master_uid, supplier_id], countdown=5)


@main.route('/products/<string:rid>/orders')
def sku_of_orders(rid):
    """某个sku订单列表"""
    per_page = request.args.get('per_page', 15, type=int)
    page = request.args.get('page', 1, type=int)
    
    builder = OrderItem.query.filter_by(sku_serial_no=rid)
    builder = builder.join(Order, OrderItem.order_id == Order.id).filter(Order.master_uid == Master.master_uid())
    
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
def repair_category_path(parent_id=0):

    Category.repair_categories(Master.master_uid(), parent_id)

    return redirect(url_for('.show_categories'))


@main.route('/categories/create', methods=['GET', 'POST'])
@user_has('admin_product')
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            master_uid=Master.master_uid(),
            name=form.name.data,
            pid=form.pid.data,
            cover_id=form.cover_id.data,
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
@user_has('admin_product')
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = EditCategoryForm(category)
    if request.method == 'POST':
        if not form.validate_on_submit():
            flash_errors(form)
            return redirect(url_for('.show_categories'))

        form.populate_obj(category)

        db.session.commit()

        # rebuild category path
        Category.repair_categories(Master.master_uid(), category.pid)

        flash('Edit category is ok!', 'success')

        return redirect(url_for('.show_categories'))

    mode = 'edit'
    form.name.data = category.name
    form.pid.data = category.pid
    form.cover_id.data = category.cover_id
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
@user_has('admin_product')
def supply_list():
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    paginated_supply = SupplyStats.query.filter_by(master_uid=Master.master_uid()).order_by(SupplyStats.created_at.desc()).paginate(
        page, per_page)
    return render_template('suppliers/supply_list.html',
                           sub_menu='purchases',
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
@user_has('admin_product')
def show_suppliers(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_suppliers = Supplier.query.filter_by(master_uid=Master.master_uid()).order_by(Supplier.created_at.desc()).paginate(page, per_page)
    return render_template('suppliers/show_list.html',
                           sub_menu='purchases',
                           paginated_suppliers=paginated_suppliers,
                           **load_common_data())


@main.route('/suppliers/create', methods=['GET', 'POST'])
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


@main.route('/products/groups', methods=['GET', 'POST'])
@main.route('/products/groups/<int:page>', methods=['GET', 'POST'])
@user_has('admin_product')
def show_product_groups(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    
    paginated_groups = ProductPacket.query.filter_by(master_uid=Master.master_uid()).order_by(ProductPacket.created_at.desc()).paginate(page, per_page)
    
    return render_template('products/show_groups.html',
                           paginated_groups=paginated_groups,
                           **load_common_data())


@main.route('/products/groups/create', methods=['GET', 'POST'])
@user_has('admin_product')
def create_product_group():
    form = ProductGroupForm()
    if form.validate_on_submit():
        if ProductPacket.query.filter_by(master_uid=Master.master_uid(), name=form.name.data).first():
            return custom_response(False, gettext('Name already exist!'))
        
        group = ProductPacket(
            master_uid=Master.master_uid(),
            name=form.name.data,
        )
        db.session.add(group)
        db.session.commit()
        
        flash(gettext('Add product group is ok!'), 'success')
        return custom_response(True)
    
    mode = 'create'
    return render_template('products/_modal_create_group.html',
                           mode=mode,
                           post_url=url_for('main.create_product_group'),
                           form=form)


@main.route('/products/groups/<int:id>/edit', methods=['GET', 'POST'])
@user_has('admin_product')
def edit_product_group(id):
    group = ProductPacket.query.get_or_404(id)
    if not Master.is_can(group.master_uid):
        abort(401)
    
    form = ProductGroupForm()
    if form.validate_on_submit():
        if group.name != form.name.data \
                and ProductPacket.query.filter_by(master_uid=Master.master_uid(), name=form.name.data).first():
            return custom_response(False, gettext('Name already exist!'))
        
        group.name = form.name.data
        
        db.session.commit()
        
        flash(gettext('Update product group is ok!'), 'success')
        return custom_response(True)
    
    mode = 'edit'
    form.name.data = group.name
    return render_template('products/_modal_create_group.html',
                           mode=mode,
                           post_url=url_for('main.edit_product_group', id=id),
                           form=form)


@main.route('/products/groups/delete', methods=['POST'])
@user_has('admin_product')
def delete_product_group():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete product group is null!', 'danger')
        abort(404)
    
    try:
        for id in selected_ids:
            group = ProductPacket.query.get_or_404(int(id))
            
            if not Master.is_can(group.master_uid):
                abort(401)
            
            db.session.delete(group)
        
        db.session.commit()
        
        flash('Delete product group is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete product group is fail!', 'danger')
    
    return redirect(url_for('.show_product_groups'))


@main.route('/products/groups/<int:id>/show', methods=['GET', 'POST'])
@user_has('admin_product')
def show_group_products(id):
    """显示组商品列表"""
    per_page = request.args.get('per_page', 10, type=int)
    page = request.args.get('page', 1, type=int)
    
    product_packet = ProductPacket.query.get_or_404(id)
    if not Master.is_can(product_packet.master_uid):
        abort(401)
    
    # 已选择商品
    builder = product_packet.products.filter_by(master_uid=Master.master_uid())
    selected_products = builder.order_by(Product.created_at.desc()).paginate(page, per_page)
    
    return render_template('products/show_set_groups.html',
                           product_group=product_packet,
                           selected_products=selected_products,
                           **load_common_data())


@main.route('/products/groups/<int:id>/products', methods=['GET', 'POST'])
@user_has('admin_product')
def ajax_product_for_group(id):
    """为商品组选择商品"""
    per_page = request.values.get('per_page', 10, type=int)
    page = request.values.get('page', 1, type=int)
    cid = request.values.get('cid', type=int)
    bid = request.values.get('bid', type=int)

    product_packet = ProductPacket.query.get_or_404(id)
    if not Master.is_can(product_packet.master_uid):
        abort(401)

    # 已选择商品
    builder = product_packet.products.filter_by(master_uid=Master.master_uid())
    selected_products = builder.order_by(Product.created_at.desc()).all()
    selected_product_ids = [p.id for p in selected_products]
    
    # 获取全部商品
    product_builder = Product.query.filter_by(master_uid=Master.master_uid())
    if bid:
        product_builder = product_builder.filter_by(brand_id=bid)
    
    if selected_product_ids:
        product_builder = product_builder.filter(Product.id.notin_(selected_product_ids))

    paginated_products = product_builder.paginate(page, per_page)
    
    brands = Brand.query.filter_by(master_uid=Master.master_uid()).all()
    categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())
    
    return render_template('products/_modal_select_products.html',
                           paginated_products=paginated_products,
                           product_packet=product_packet,
                           categories=categories,
                           brands=brands,
                           bid=bid,
                           cid=cid)


@main.route('/products/groups/<int:id>/submit', methods=['POST'])
@user_has('admin_product')
def submit_product_for_group(id):
    rid = request.values.get('rid')
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids and not rid:
        return custom_response(False, gettext("Product isn't null!"))
    
    product_packet = ProductPacket.query.get_or_404(id)
    if not Master.is_can(product_packet.master_uid):
        return custom_response(False, gettext("Product can't authorization!"))

    product_list = []
    if rid:
        product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first()
        if product is None:
            return custom_response(False, gettext("Product isn't exist!"))
        product_list.append(product)
    
    if selected_ids:
        product_list = Product.query.filter_by(master_uid=Master.master_uid())\
            .filter(Product.serial_no.in_(selected_ids)).all()
    
    product_packet.push_product(*product_list)
    
    db.session.commit()
    
    return status_response(True, gettext("Select product is ok!"))


@main.route('/products/groups/<int:id>/remove', methods=['POST'])
@user_has('admin_product')
def remove_product_from_group(id):
    rid = request.values.get('rid')
    if not rid:
        return custom_response(False, gettext("Product isn't null!"))
    
    product_packet = ProductPacket.query.get_or_404(id)
    if not Master.is_can(product_packet.master_uid):
        return custom_response(False, gettext("Product can't authorization!"))

    product_list = []
    if rid:
        product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first()
        if product is None:
            return custom_response(False, gettext("Product isn't exist!"))
        product_list.append(product)
        
    product_packet.remove_product(*product_list)

    db.session.commit()

    return status_response(True, gettext("Cancel select is ok!"))


@main.route('/products/discount_templets')
@main.route('/products/discount_templets/<int:page>')
def show_discount_templets(page=1):
    """经销折扣等级"""
    per_page = request.args.get('per_page', 10, type=int)

    paginated_discount_templets = DiscountTemplet.query.filter_by(master_uid=Master.master_uid()) \
        .order_by(DiscountTemplet.created_at.desc()).paginate(page, per_page)

    return render_template('products/show_discount_templets.html',
                           paginated_discount_templets=paginated_discount_templets,
                           **load_common_data())


@main.route('/products/discount_templets/create', methods=['GET', 'POST'])
def create_discount_templet():
    form = DiscountTempletForm()
    form.type.choices = [(1, gettext('By Category')), (2, gettext('By Brand'))]
    if form.validate_on_submit():
        discount_templet = DiscountTemplet(
            master_uid=Master.master_uid(),
            name=form.name.data,
            default_discount=form.default_discount.data,
            type=form.type.data,
            description=form.description.data
        )
        db.session.add(discount_templet)
        db.session.commit()

        flash(gettext('Add Discount Templet is ok!'), 'success')

        return redirect(url_for('main.show_discount_templets'))

    mode = 'create'
    return render_template('products/create_edit_templet.html',
                           mode=mode,
                           form=form)


@main.route('/products/discount_templets/<int:id>/edit', methods=['GET', 'POST'])
def edit_discount_templet(id):
    discount_templet = DiscountTemplet.query.get_or_404(id)
    if not Master.is_can(discount_templet.master_uid):
        abort(401)

    form = DiscountTempletEditForm()
    if form.validate_on_submit():

        discount_templet.name = form.name.data
        discount_templet.default_discount = form.default_discount.data
        discount_templet.description = form.description.data

        db.session.commit()

        flash(gettext('Update Discount Templet is ok!'), 'success')

        return redirect(url_for('main.show_discount_templets'))
    else:
        current_app.logger.warn(form.errors)

    mode = 'edit'

    form.name.data = discount_templet.name
    form.default_discount.data = discount_templet.default_discount
    form.description.data = discount_templet.description

    return render_template('products/create_edit_templet.html',
                           mode=mode,
                           form=form)


@main.route('/products/discount_templets/delete', methods=['POST'])
def delete_discount_templet():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete discount template is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            discount_templet = DiscountTemplet.query.get_or_404(int(id))
            if not Master.is_can(discount_templet.master_uid):
                abort(401)

            db.session.delete(discount_templet)

        db.session.commit()

        flash('Delete discount template is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete discount template is fail!', 'danger')

    return redirect(url_for('.show_discount_templets'))


@main.route('/products/discount_templets/<int:id>/set_discount', methods=['GET', 'POST'])
def set_discount(id):
    """设置折扣值"""
    discount_templet = DiscountTemplet.query.get_or_404(id)
    if not Master.is_can(discount_templet.master_uid):
        abort(401)

    categories = []
    brands = []
    selected_items = {}

    if request.method == 'POST':
        categories = request.form.getlist('categories[]')
        brands = request.form.getlist('brands[]')
        valid_discount = []
        for cid in categories:
            discount = request.form.get('discount_%s' % cid, type=float)
            if discount:
                item = DiscountTempletItem(
                    master_uid=Master.master_uid(),
                    category_id=cid,
                    discount=discount
                )
                valid_discount.append(item)

        for bid in brands:
            discount = request.form.get('discount_%s' % bid, type=float)
            if discount:
                item = DiscountTempletItem(
                    master_uid=Master.master_uid(),
                    brand_id=bid,
                    discount=discount
                )
                valid_discount.append(item)

        if len(valid_discount):
            discount_templet.items = valid_discount

        db.session.commit()

        flash(gettext('Set Discount is ok!'), 'success')

        return redirect(url_for('main.show_discount_templets'))

    # 按分类
    if discount_templet.type == 1:
        categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())

        for item in discount_templet.items:
            selected_items[item.category_id] = item.discount

    # 按品牌
    if discount_templet.type == 2:
        brands = Brand.query.filter_by(master_uid=Master.master_uid()).all()

        for item in discount_templet.items:
            selected_items[item.brand_id] = item.discount

    return render_template('products/set_discount.html',
                           discount_templet=discount_templet,
                           selected_items=selected_items,
                           categories=categories,
                           brands=brands)


@main.route('/products/download_wxacode', methods=['GET', 'POST'])
def download_wxacode():
    """下载商品小程序码"""
    rid = request.values.get('rid')
    size = {
        '8cm': 576,
        '12cm': 864,
        '15cm': 1080,
        '30cm': 2160,
        '50cm': 3600
    }
    if request.method == 'POST':
        cm = request.form.get('cm')
        width = size[cm]
        path = 'pages/product/product'

        # 商品是否存在
        product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first_or_404()

        # 小程序名称
        wxa = WxMiniApp.query.filter_by(master_uid=Master.master_uid()).first_or_404()

        auth_app_id = wxa.auth_app_id

        try:
            # 获取授权信息
            authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()
            # 获得小程序码
            open3rd = WxaOpen3rd(access_token=authorizer.access_token)
            result = open3rd.get_wxacode_unlimit(path, scene=rid, width=width)
        except WxAppError as err:
            current_app.logger.warn('Wxapp wxacode is error: %s' % err)
            return status_response(False, {
                'code': 500,
                'message': str(err)
            })

        # 构建鉴权对象
        cfg = current_app.config
        q = Auth(cfg['QINIU_ACCESS_KEY'], cfg['QINIU_ACCESS_SECRET'])

        # 上传到七牛后保存的文件名
        key = 'qrcode/wxacode-%s-%s.jpg' % (rid, hashlib.md5(path.encode(encoding='UTF-8')).hexdigest())
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(cfg['QINIU_BUCKET_NAME'], key, 3600)
        # 开始上传
        ret, info = put_data(token, key, result.content)

        current_app.logger.warn('ret: %s' % ret)
        current_app.logger.warn('info: %s' % info)

        # 生成小程序码
        wxa_image_url = '%s/%s' % (Asset.host_url(), key)



    return render_template('products/_modal_wxacode.html')


@main.route('/products/make_poster', methods=['GET', 'POST'])
def make_adv_poster():
    """生成宣传海报图"""
    rid = request.values.get('rid')

    return render_template('products/_modal_poster.html')
