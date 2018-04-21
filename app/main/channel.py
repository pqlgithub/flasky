# -*- coding: utf-8 -*-
from flask import g, render_template, redirect, url_for, abort, flash, request, current_app
from flask_babelex import gettext
from sqlalchemy.exc import DataError
from . import main
from .. import db
from app.models import Store, Product, User, UserIdType, STORE_TYPE, Banner, BannerImage, LINK_TYPES, Brand,\
    ProductPacket, DiscountTemplet, StoreDistributeProduct, StoreDistributePacket, Category, Warehouse, STORE_MODES, \
    StoreProduct
from app.forms import StoreForm, BannerForm, BannerImageForm
from ..utils import custom_status, R200_OK, R201_CREATED, Master, status_response, R400_BADREQUEST, custom_response, \
    correct_decimal, correct_int
from ..helpers import MixGenId
from ..decorators import user_has


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'stores'
    }


@main.route('/stores')
@user_has('admin_setting')
def show_stores():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    platform = request.args.get('platform', type=int)

    builder = Store.query.filter_by(master_uid=Master.master_uid())
    if platform:
        builder = builder.filter_by(platform=platform)

    paginated_stores = builder.order_by(Store.id.asc()).paginate(page, per_page)
    
    return render_template('stores/show_list.html',
                           sub_menu='stores',
                           platform=platform,
                           paginated_stores=paginated_stores,
                           **load_common_data())


@main.route('/stores/create', methods=['GET', 'POST'])
@user_has('admin_setting')
def create_store():
    form = StoreForm()
    form.type.choices = STORE_TYPE
    form.distribute_mode.choices = STORE_MODES

    # 设置关联负责人
    user_choices = []
    # 主账号
    master = User.query.get(Master.master_uid())
    user_choices.append((master.id, master.username))

    user_list = User.query.filter_by(master_uid=Master.master_uid(), id_type=UserIdType.SUPPLIER).all()
    for user in user_list:
        user_choices.append((user.id, user.username))

    form.operator_id.choices = user_choices
    
    if form.validate_on_submit():
        if Store.validate_unique_name(form.name.data, Master.master_uid(), form.platform.data):
            flash('Store name already exist!', 'danger')
            return redirect(url_for('.create_store'))

        try:
            store = Store(
                master_uid=Master.master_uid(),
                name=form.name.data,
                serial_no=MixGenId.gen_store_sn(),
                platform=form.platform.data,
                operator_id=form.operator_id.data,
                type=form.type.data,
                description=form.description.data,
                distribute_mode=form.distribute_mode.data,
                is_private_stock=form.is_private_stock.data,
                status=form.status.data
            )
            db.session.add(store)

            # 同步设置虚拟私有仓库
            if form.is_private_stock.data:
                virtual_warehouse = Warehouse.query.filter_by(master_uid=Master.master_uid(), store_id=store.id).first()
                if virtual_warehouse is None:
                    virtual_warehouse = Warehouse(
                        master_uid=Master.master_uid(),
                        name=form.name.data,
                        store_id=store.id,
                        type=3
                    )
                    db.session.add(virtual_warehouse)

            db.session.commit()

            flash('Add store is success!', 'success')

            return redirect(url_for('.show_stores'))
        except Exception as err:
            db.session.rollback()
            current_app.logger.warn('Add store fail: %s' % str(err))

    return render_template('stores/create_and_edit.html',
                           form=form,
                           sub_menu='stores',
                           **load_common_data())


@main.route('/stores/<int:id>/edit', methods=['GET', 'POST'])
@user_has('admin_setting')
def edit_store(id):
    store = Store.query.get_or_404(id)
    if not Master.is_can(store.master_uid):
        abort(401)
    
    form = StoreForm()
    form.type.choices = STORE_TYPE
    form.distribute_mode.choices = STORE_MODES

    # 设置关联负责人
    user_choices = []
    # 主账号
    master = User.query.get(Master.master_uid())
    user_choices.append((master.id, master.username))

    user_list = User.query.filter_by(master_uid=Master.master_uid(), id_type=UserIdType.SUPPLIER).all()
    for user in user_list:
        user_choices.append((user.id, user.username))

    form.operator_id.choices = user_choices

    if form.validate_on_submit():
        old_store = Store.validate_unique_name(form.name.data, Master.master_uid(), form.platform.data)
        if old_store and old_store.id != id:
            flash('Store name already exist!', 'danger')
            return redirect(url_for('.edit_store', id=id))

        form.populate_obj(store)

        # 同步设置虚拟私有仓库
        if form.is_private_stock.data:
            virtual_warehouse = Warehouse.query.filter_by(master_uid=Master.master_uid(), store_id=store.id).first()
            if virtual_warehouse is None:
                virtual_warehouse = Warehouse(
                    master_uid=Master.master_uid(),
                    name=form.name.data,
                    store_id=store.id,
                    type=3
                )
                db.session.add(virtual_warehouse)
            else:
                virtual_warehouse.name = form.name.data
        
        db.session.commit()

        flash('Edit store is success!', 'success')
        return redirect(url_for('.show_stores'))

    # 填充数据
    form.name.data = store.name
    form.platform.data = store.platform
    form.operator_id.data = store.operator_id
    form.type.data = store.type
    form.description.data = store.description
    form.distribute_mode.data = store.distribute_mode
    form.is_private_stock.data = store.is_private_stock
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


@main.route('/stores/product/distribute', methods=['GET', 'POST'])
def store_distribute_products():
    """单个为店铺授权商品"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    rid = request.values.get('rid')
    _type = request.values.get('type', 'selected')
    cid = request.values.get('cid', type=int)
    bid = request.values.get('bid', type=int)

    store = Store.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first_or_404()

    # 已选择商品
    distribute_builder = StoreProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id)

    # 搜索筛选
    brands = Brand.query.filter_by(master_uid=Master.master_uid()).all()
    categories = Category.always_category(path=0, page=1, per_page=1000, uid=Master.master_uid())

    selected_products = []
    selected_product_ids = []
    paginated_products = {}
    if _type == 'all':
        distributed_products = distribute_builder.all()
        selected_product_ids = [item.id for item in distributed_products]

        # 获取全部商品
        if cid:
            category = Category.query.get(cid)
            if category is None or category.master_uid != g.master_uid:
                abort(404)
            product_builder = category.products.filter_by(master_uid=Master.master_uid())
        else:
            product_builder = Product.query.filter_by(master_uid=Master.master_uid())

        if bid:
            product_builder = product_builder.filter_by(brand_id=bid)

        if selected_product_ids:
            product_builder = product_builder.filter(Product.id.notin_(selected_product_ids))

        paginated_products = product_builder.paginate(page, per_page)
    else:
        distributed_products = distribute_builder.paginate(page, per_page)
        for item in distributed_products.items:
            product = Product.query.get(item.product_id)
            if product is None:
                continue
            extra_data = StoreDistributeProduct.query.filter_by(product_id=item.product_id).all()
            if extra_data:
                sku_modes = {}
                for sku in product.skus:
                    sku_modes[sku.serial_no] = sku.mode

                renew_extra_data = []
                for extra in extra_data:
                    extra.mode = sku_modes.get(extra.sku_serial_no)
                    renew_extra_data.append(extra)

                product.extra_data = renew_extra_data
            selected_products.append(product)

        distributed_products.items = selected_products

    return render_template('stores/distribute_products.html',
                           paginated_products=paginated_products,
                           distributed_products=distributed_products,
                           selected_product_ids=selected_product_ids,
                           selected_products=selected_products,
                           categories=categories,
                           brands=brands,
                           store=store,
                           type=_type,
                           bid=bid,
                           cid=cid)


@main.route('/stores/product/distribute_stock', methods=['GET', 'POST'])
def ajax_distribute_stock():
    """更新授权商品库存"""
    rid = request.values.get('rid')
    product_rid = request.values.get('product_rid')

    # 验证商品是否存在
    product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=product_rid).first_or_404()

    store = Store.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first_or_404()

    if request.method == 'POST':
        for sku in product.skus:
            sku_stock = request.form.get('sku_stock_%s' % sku.serial_no)
            sku_stock = correct_int(sku_stock)
            if sku_stock == 0:  # 跳过
                continue

            distribute_sku = StoreDistributeProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id,
                                                                    sku_id=sku.id).first()
            if not distribute_sku:
                distribute_sku = StoreDistributeProduct(
                    master_uid=Master.master_uid(),
                    store_id=store.id,
                    product_id=product.id,
                    product_serial_no=product.serial_no,
                    sku_id=sku.id,
                    sku_serial_no=sku.serial_no,
                    private_stock=sku_stock
                )
                
                db.session.add(distribute_sku)
            else:  # 更新库存
                distribute_sku.private_stock = sku_stock

        db.session.commit()

        return status_response()

    extra_data = {}
    # 获取sku扩展数据
    extra_skus = StoreDistributeProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id,
                                                        product_id=product.id).all()
    for extra_sku in extra_skus:
        extra_data[extra_sku.sku_serial_no] = {
            'private_stock': extra_sku.private_stock
        }

    return render_template('stores/_extra_stock_modal.html',
                           extra_data=extra_data,
                           product=product,
                           rid=store.serial_no,
                           product_rid=product_rid)


@main.route('/stores/product/distribute_price', methods=['GET', 'POST'])
def ajax_distribute_price():
    """更新授权商品的价格"""
    rid = request.values.get('rid')
    product_rid = request.values.get('product_rid')

    # 验证商品是否存在
    product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=product_rid).first_or_404()

    store = Store.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first_or_404()
    if request.method == 'POST':
        for sku in product.skus:
            sku_price = request.form.get('sku_price_%s' % sku.serial_no)
            sku_sale_price = request.form.get('sku_sale_price_%s' % sku.serial_no)

            current_app.logger.debug('sku price: %s, sale_price: %s' % (sku_price, sku_sale_price))

            sku_price = correct_decimal(sku_price)
            sku_sale_price = correct_decimal(sku_sale_price)

            # 跳过
            if sku_price == 0 and sku_sale_price == 0:
                continue

            distribute_sku = StoreDistributeProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id,
                                                                    sku_id=sku.id).first()
            if not distribute_sku:
                distribute_sku = StoreDistributeProduct(
                    master_uid=Master.master_uid(),
                    store_id=store.id,
                    product_id=product.id,
                    product_serial_no=product.serial_no,
                    sku_id=sku.id,
                    sku_serial_no=sku.serial_no,
                    price=sku_price,
                    sale_price=sku_sale_price
                )

                db.session.add(distribute_sku)
            else:  # 更新价格
                distribute_sku.price = sku_price
                distribute_sku.sale_price = sku_sale_price

        db.session.commit()

        return status_response()

    # 获取sku扩展数据
    extra_skus = StoreDistributeProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id,
                                                        product_id=product.id).all()
    extra_data = {}
    for extra_sku in extra_skus:
        extra_data[extra_sku.sku_serial_no] = {
            'price': extra_sku.price,
            'sale_price': extra_sku.sale_price
        }

    current_app.logger.warn(extra_data)

    return render_template('stores/_extra_price_modal.html',
                           extra_data=extra_data,
                           product=product,
                           rid=store.serial_no,
                           product_rid=product_rid)


@main.route('/stores/product/ajax_distribute', methods=['POST'])
def ajax_distribute_product():
    """授权操作"""
    rid = request.values.get('rid')
    product_rid = request.values.get('product_rid')
    try:
        # 验证商品是否存在
        product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=product_rid).first_or_404()
        store = Store.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first_or_404()

        store_product = StoreProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id,
                                                     product_id=product.id).first()
        if store_product is None:
            store_product = StoreProduct(
                master_uid=Master.master_uid(),
                store_id=store.id,
                product_id=product.id
            )
            db.session.add(store_product)

        db.session.commit()
    except Exception as err:
        db.session.rollback()
        current_app.logger.warn('Store add product: %s' % str(err))
        return custom_response(False, '店铺添加产品失败')

    return custom_response(True, '店铺添加产品成功')


@main.route('/stores/product/remove', methods=['POST'])
def remove_product_from_store():
    rid = request.values.get('rid')
    product_rid = request.values.get('product_rid')
    if not product_rid:
        return custom_response(False, gettext("Product isn't null!"))

    try:
        # 验证商品是否存在
        product = Product.query.filter_by(master_uid=Master.master_uid(), serial_no=product_rid).first_or_404()
        store = Store.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first_or_404()

        store_product = StoreProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id,
                                                     product_id=product.id).first()
        if store_product:
            db.session.delete(store_product)

            # 同步删除私有信息
            product_list = StoreDistributeProduct.query.filter_by(master_uid=Master.master_uid(), store_id=store.id,
                                                                  product_id=product.id).all()
            for pp in product_list:
                db.session.delete(pp)

            db.session.commit()
    except Exception as err:
        db.session.rollback()
        current_app.logger.warn('From store delete product: %s' % str(err))
        return custom_response(False, '从店铺删除产品失败')

    return custom_response(True, gettext("Cancel select is ok!"))


@main.route('/stores/<string:rid>/distribute_by_packet', methods=['GET', 'POST'])
def distribute_products_by_packet(rid):
    """通过商品组批量为店铺授权商品"""
    store = Store.query.filter_by(master_uid=Master.master_uid(), serial_no=rid).first_or_404()
    if request.method == 'POST':
        selected_ids = request.form.getlist('selected[]')

        for packet_id in selected_ids:
            discount_templet_id = request.form.get('discount_tpl_%s' % packet_id)
            if discount_templet_id:
                # 检测是否设置
                distribute_packet = StoreDistributePacket.query.filter_by(master_uid=Master.master_uid(),
                                                                          store_id=store.id,
                                                                          product_packet_id=packet_id).first()
                if distribute_packet is None:
                    # 新增
                    new_distribute_packet = StoreDistributePacket(
                        master_uid=Master.master_uid(),
                        store_id=store.id,
                        product_packet_id=packet_id,
                        discount_templet_id=discount_templet_id
                    )
                    db.session.add(new_distribute_packet)
                else:
                    # 更新
                    distribute_packet.discount_templet_id = discount_templet_id

        db.session.commit()

        return status_response(True, gettext('Distribute products is ok!'))

    product_packets = ProductPacket.query.filter_by(master_uid=Master.master_uid()).all()
    discount_templets = DiscountTemplet.query.filter_by(master_uid=Master.master_uid()).all()

    # 已分发商品组
    distributed_packet = {}
    for dp in store.distribute_packets.all():
        distributed_packet[dp.product_packet_id] = dp.discount_templet_id

    return render_template('stores/_modal_distribute.html',
                           product_packets=product_packets,
                           discount_templets=discount_templets,
                           distributed_packet=distributed_packet,
                           post_url=url_for('main.store_distribute_products', rid=rid))


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
                               sub_menu='banner',
                               p=p,
                               qk=qk,
                               sk=sk,
                               **load_common_data())
    
    # 正常列表
    builder = BannerImage.query.filter_by(master_uid=Master.master_uid())
    paginated_banners = builder.order_by(BannerImage.created_at.desc()).paginate(page, per_page)
    
    spot_list = Banner.query.filter_by(master_uid=Master.master_uid()).all()
    
    return render_template('banners/show_list.html',
                           sub_menu='banner',
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
                           sub_menu='banner',
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
                           sub_menu='banner',
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


@main.route('/banners/spots', methods=['GET', 'POST'])
@user_has('admin_setting')
def show_spots():
    """banner位置列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 20, type=int)

    builder = Banner.query.filter_by(master_uid=Master.master_uid())
    paginated_spots = builder.order_by(Banner.created_at.desc()).paginate(page, per_page)

    return render_template('banners/show_spots.html',
                           sub_menu='banners',
                           paginated_spots=paginated_spots,
                           **load_common_data())


@main.route('/banners/spots/create', methods=['GET', 'POST'])
@user_has('admin_setting')
def create_spot():
    """新增banner位置"""
    form = BannerForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                spot = Banner(
                    master_uid=Master.master_uid(),
                    serial_no=form.serial_no.data,
                    name=form.name.data,
                    width=form.width.data,
                    height=form.height.data,
                    status=1
                )
                db.session.add(spot)
                db.session.commit()
            except DataError as err:
                current_app.logger.warn('Create banner spot error: %s!' % repr(err))
                db.session.rollback()
                return status_response(False, R400_BADREQUEST)

            return status_response(True, R201_CREATED)
        else:
            current_app.logger.warn(form.errors)
            return custom_status('error', 400)
    
    mode = 'create'
    return render_template('banners/_modal_spot_create.html',
                           post_url=url_for('.create_spot'),
                           mode=mode,
                           form=form)


@main.route('/banners/spots/<string:rid>/edit', methods=['GET', 'POST'])
@user_has('admin_setting')
def edit_spot(rid):
    """更新banner位置"""
    spot = Banner.query.filter_by(serial_no=rid).first()
    form = BannerForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                form.populate_obj(spot)

                db.session.commit()
            except DataError as err:
                current_app.logger.warn('Edit banner spot error: %s!' % repr(err))
                db.session.rollback()
                return status_response(False, R400_BADREQUEST)

            return status_response(True, R200_OK)
        else:
            current_app.logger.warn(form.errors)
            return custom_status('error', 400)

    mode = 'mode'
    form.name.data = spot.name
    form.serial_no.data = spot.serial_no
    form.width.data = spot.width
    form.height.data = spot.height
    return render_template('banners/_modal_spot_create.html',
                           post_url=url_for('.edit_spot', rid=rid),
                           mode=mode,
                           form=form)
