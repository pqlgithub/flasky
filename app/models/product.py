# -*- coding: utf-8 -*-
from sqlalchemy import text, event
from sqlalchemy.sql import func
from flask_babelex import gettext, lazy_gettext
from jieba.analyse.analyzer import ChineseAnalyzer
from app import db, uploader
from ..utils import timestamp, gen_serial_no, create_db_session
from .asset import Asset
from ..constant import DEFAULT_IMAGES
from .purchase import Purchase
from .store import Currency

__all__ = [
    'Product',
    'ProductSku',
    'ProductStock',
    'CustomsDeclaration',
    'Brand',
    'Supplier',
    'SupplyStats',
    'Category',
    'CategoryPath'
]


# 海关危险品
DANGEROUS_GOODS_TYPES = [
    ('N', gettext('No')),
    ('D', gettext('Electricity')), # 含电
    ('Y', gettext('Liquid')), # 液体
    ('F', gettext('Powder')) # 粉末
]

# 供应商合作方式
BUSINESS_MODE = [
    ('C', gettext('Direct purchasing'), lazy_gettext('Direct purchasing')), # 直采
    ('D', gettext('Proxy'), lazy_gettext('Proxy')), # 代理
    ('Q', gettext('Exclusive'), lazy_gettext('Exclusive')) # 独家
]

# 产品的状态
PRODUCT_STATUS = [
    (1, lazy_gettext('Enabled'), 'success'),
    (-1, lazy_gettext('Disabled'), 'danger')
]

# product and category => N to N
product_category_table = db.Table('categories_products',
                    db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
                    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
                )


class Product(db.Model):
    """产品信息"""

    __tablename__ = 'products'

    __searchable__ = ['serial_no', 'name', 'description', 'supplier_name', 'all_sku']
    __analyzer__ = ChineseAnalyzer()

    id = db.Column(db.Integer, primary_key=True)
    # 产品编号
    serial_no = db.Column(db.String(12), unique=True, index=True, nullable=False)
    master_uid = db.Column(db.Integer, index=True, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))

    name = db.Column(db.String(128), nullable=False)
    cover_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    # 识别码
    id_code = db.Column(db.String(16), nullable=True)
    # 币种
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'))
    # 采购价
    cost_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 零售价
    sale_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 用于出库称重和利润计算
    s_weight = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    s_length = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    s_width = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    s_height = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 来源URL
    from_url = db.Column(db.String(255), nullable=True)
    type = db.Column(db.SmallInteger, default=1)
    status = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text())

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # product and sku => 1 to N
    skus = db.relationship(
        'ProductSku', backref='product', lazy='dynamic'
    )

    # product and customs declaration => 1 to 1
    declaration = db.relationship(
        'CustomsDeclaration', backref='product', uselist=False
    )

    @property
    def currency_unit(self):
        """当前货币单位"""
        if self.currency_id:
            current_currency = Currency.query.get(self.currency_id)
            return current_currency.code
        else:
            return None
    
    @property
    def supplier_name(self):
        current_supplier = self.supplier
        return '{} {}'.format(current_supplier.short_name, current_supplier.full_name)

    @property
    def all_sku(self):
        """全部SKU"""
        sku_list = [sku.serial_no for sku in self.skus]
        return ' '.join(sku_list)

    @property
    def status_label(self):
        for s in PRODUCT_STATUS:
            if s[0] == self.status:
                return s

    @property
    def cover(self):
        """cover asset info"""
        return Asset.query.get(self.cover_id) if self.cover_id else None

    @property
    def category_ids(self):
        """获取所属的分类ID"""
        return [category.id for category in self.categories]

    def add_categories(self, *categories):
        """追加所属分类"""
        self.categories.extend([category for category in categories if category not in self.categories])

    def update_categories(self, *categories):
        """更新所属分类"""
        self.categories = [category for category in categories]

    def remove_categories(self, *categories):
        """删除所属分类"""
        self.categories = [category for category in self.categories if category not in categories]

    @staticmethod
    def make_unique_serial_no(serial_no):
        if Product.query.filter_by(serial_no=serial_no).first() == None:
            return serial_no
        while True:
            new_serial_no = gen_serial_no()
            if Product.query.filter_by(serial_no=new_serial_no).first() == None:
                break
        return new_serial_no

    def __repr__(self):
        return '<Product %r>' % self.name


class ProductSku(db.Model):
    """产品的SKU"""

    __tablename__ = 'product_skus'

    __searchable__ = ['serial_no', 'product_name', 'supplier_name']
    __analyzer__ = ChineseAnalyzer()

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    # 产品编号sku
    serial_no = db.Column(db.String(12), unique=True, index=True, nullable=False)
    cover_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    s_model = db.Column(db.String(64), nullable=False)
    # 重量
    s_weight = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 采购价
    cost_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 零售价
    sale_price = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 备注
    remark = db.Column(db.String(255), nullable=True)
    # 状态：-1、取消或缺省状态； 1、正常（默认）
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # 第三方平台编号
    outside_serial_no = db.Column(db.String(20), index=True, nullable=True)

    # sku and stock => 1 to N
    stocks = db.relationship(
        'ProductStock', backref='product_sku', lazy='dynamic'
    )

    @property
    def product_name(self):
        """product name"""
        return self.product.name

    @property
    def supplier_name(self):
        """supplier name"""
        return '{} {}'.format(self.supplier.short_name, self.supplier.full_name)


    @property
    def cover(self):
        """cover asset info"""
        return Asset.query.get(self.cover_id) if self.cover_id else DEFAULT_IMAGES['cover']

    @property
    def stock_count(self):
        """product sku stock count"""
        return ProductStock.stock_count_of_product(self.id)

    @staticmethod
    def make_unique_serial_no(serial_no):
        if ProductSku.query.filter_by(serial_no=serial_no).first() == None:
            return serial_no
        while True:
            new_serial_no = gen_serial_no()
            if ProductSku.query.filter_by(serial_no=new_serial_no).first() == None:
                break
        return new_serial_no

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_sku = {
            'id': self.id,
            'serial_no': self.serial_no,
            's_model': self.s_model,
            'cover': uploader.url(self.cover.filepath),
            'cost_price': str(self.cost_price),
            's_weight': str(self.s_weight)
        }
        return json_sku

    def __repr__(self):
        return '<ProductSku %r>' % self.serial_no


class ProductStock(db.Model):
    """产品库存数"""

    __tablename__ = 'product_stocks'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'), index=True)
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), index=True)
    warehouse_shelve_id = db.Column(db.Integer, db.ForeignKey('warehouse_shelves.id'))

    # 库存累计总数
    total_count = db.Column(db.Integer, default=0)
    # 当前库存数
    current_count = db.Column(db.Integer, default=0)
    # 预售库存数
    presale_count = db.Column(db.Integer, default=0)
    # 已销售数
    saled_count = db.Column(db.Integer, default=0)
    # 残次品数量
    defective_count = db.Column(db.Integer, default=0)
    # 退换数量
    returned_count = db.Column(db.Integer, default=0)
    # 手动数量
    manual_count = db.Column(db.Integer, default=0)

    # 库存预警设置
    min_count = db.Column(db.Integer, default=0)
    max_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # stock and product_sku => 1 to 1
    sku = db.relationship(
        'ProductSku', backref='product_stock', uselist=False
    )

    @property
    def cover(self):
        """获取对应产品的封面图"""
        sku = self.sku
        if not sku:
            return DEFAULT_IMAGES['cover']
        return sku.cover


    @property
    def available_count(self):
        """当前某个仓库某个产品的有效库存数量"""
        return self.current_count - self.presale_count

    @property
    def out_of_stock(self):
        """库存不足状态"""
        return self.current_count <= self.min_count

    @property
    def purchasing_count(self):
        """已采购未到货的数量"""
        return 0

    @staticmethod
    def validate_is_exist(warehouse_id, sku_id):
        return ProductStock.query.filter_by(warehouse_id=warehouse_id, product_sku_id=sku_id).first()

    @staticmethod
    def validate_stock_quantity(warehouse_id, sku_id, quantity=1):
        stock = ProductStock.query.filter_by(warehouse_id=warehouse_id, product_sku_id=sku_id).one()
        return stock.current_count >= quantity

    @staticmethod
    def get_stock_quantity(warehouse_id, sku_id):
        """获取某个仓库某个产品的有效库存数量"""
        stock = ProductStock.query.filter_by(warehouse_id=warehouse_id, product_sku_id=sku_id).first()
        return stock.current_count if stock else 0

    @staticmethod
    def stock_count_of_product(sku_id):
        """获取某个产品所有仓库的库存总数"""
        total_quantity = ProductStock.query.filter_by(product_sku_id=sku_id).with_entities(func.sum(ProductStock.current_count)).one()

        return total_quantity[0] if (total_quantity and total_quantity[0] is not None) else 0


    def __repr__(self):
        return '<ProductStock %r>' % self.id



class CustomsDeclaration(db.Model):
    """报关信息"""

    __tablename__ = 'customs_declarations'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    dangerous_goods = db.Column(db.String(1), default='N')
    local_name = db.Column(db.String(100), nullable=False)
    en_name = db.Column(db.String(100), nullable=False)
    s_weight = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 海关编码
    customs_code = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<Customs %r>' % self.local_name


class Supplier(db.Model):
    """供应商信息"""

    __tablename__ = 'suppliers'

    __searchable__ = ['short_name', 'full_name', 'contact_name', 'address', 'phone']
    __analyzer__ = ChineseAnalyzer()

    id = db.Column(db.Integer, primary_key=True)
    # master user id
    master_uid = db.Column(db.Integer, index=True, default=0)
    # 简称
    short_name = db.Column(db.String(100), index=True, nullable=False)
    # 全称
    full_name = db.Column(db.String(50), index=True, nullable=False)
    # 合作方式
    type = db.Column(db.String(1), index=True, default='C')
    # 合作开始日期
    start_date = db.Column(db.Date, nullable=False)
    # 合作结束日期
    end_date = db.Column(db.Date, nullable=False)
    # 联系人
    contact_name = db.Column(db.String(32))
    # 地址
    address = db.Column(db.String(100))
    # 电话
    phone = db.Column(db.String(20))
    # 备注
    remark = db.Column(db.String(255))
    # 默认供应商
    is_default = db.Column(db.Boolean, default=False)

    time_limit = db.Column(db.String(50), nullable=True)
    business_scope = db.Column(db.Text(), nullable=True)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # supplier and brand => 1 to N
    brands = db.relationship(
        'Brand', backref='supplier', lazy='dynamic'
    )

    # supplier and product => 1 to N
    products = db.relationship(
        'Product', backref='supplier', lazy='dynamic'
    )
    # supplier and product sku => 1 to N
    skus = db.relationship(
        'ProductSku', backref='supplier', lazy='dynamic'
    )

    # supplier and purchase => 1 to N
    purchases = db.relationship(
        'Purchase', backref='supplier', lazy='dynamic'
    )

    # supplier and stats => 1 to N
    supply_stats = db.relationship(
        'SupplyStats', backref='supplier', lazy='dynamic'
    )

    @property
    def desc_type(self):
        for t in BUSINESS_MODE:
            if t[0] == self.type:
                return t

    def __repr__(self):
        return '<Supplier %r>' % self.full_name


    def to_json(self):
        """资源和JSON的序列化转换"""
        return {
            c.name: getattr(self, c.name, None) for c in self.__table__.columns
        }


class SupplyStats(db.Model):
    """供货关系"""

    __tablename__ = 'supply_relevance'

    __searchable__ = ['supplier_name']
    __analyzer__ = ChineseAnalyzer()

    __table_args__ = (
        db.UniqueConstraint('master_uid', 'supplier_id', name='uix_supply_master_uid_supplier_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    sku_count = db.Column(db.Integer, default=0)
    purchase_times = db.Column(db.Integer, default=0)
    purchase_amount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    latest_trade_at = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)


    @property
    def supplier_name(self):
        return '{} {}'.format(self.supplier.short_name, self.supplier.full_name)


    @staticmethod
    def on_sync_change(mapper, connection, target):
        """同步数据事件"""
        master_uid = target.master_uid
        supplier_id = target.supplier_id

        session = create_db_session()
        # session.query(User).limit(n).all()
        # session.execute('select * from user where id = :id', {'id': 1}).first()

        # 1、统计sku count
        sku_count = ProductSku.query.filter_by(master_uid=master_uid, supplier_id=supplier_id).count()

        # 2、统计purchase / 总收入
        purchase_result = Purchase.query.filter_by(master_uid=master_uid, supplier_id=supplier_id)\
            .with_entities(func.count(Purchase.id), func.sum(Purchase.total_amount), func.max(Purchase.created_at))\
            .one()

        purchase_amount = purchase_result[1] if purchase_result[1] is not None else 0
        latest_trade_at = purchase_result[2] if purchase_result[2] is not None else 0

        # 3、同步数据
        supply_stats = session.query(SupplyStats).filter_by(master_uid=master_uid, supplier_id=supplier_id).first()
        if supply_stats:
            query = session.query(SupplyStats).filter_by(master_uid=master_uid, supplier_id=supplier_id)
            query.update({
                SupplyStats.sku_count: sku_count,
                SupplyStats.purchase_times: purchase_result[0],
                SupplyStats.purchase_amount: purchase_amount,
                SupplyStats.latest_trade_at: latest_trade_at
            })
        else:
            supply_stats = SupplyStats(
                master_uid = master_uid,
                supplier_id = supplier_id,
                sku_count = sku_count,
                purchase_times = purchase_result[0],
                purchase_amount = purchase_amount,
                latest_trade_at = latest_trade_at
            )
            session.add(supply_stats)

        session.commit()


    def __repr__(self):
        return '<SupplyStats %r>' % self.supplier_id



class Brand(db.Model):
    """品牌信息"""

    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)

    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))

    master_uid = db.Column(db.Integer, index=True, default=0)
    name = db.Column(db.String(64), unique=True, index=True)
    features = db.Column(db.String(100))
    description = db.Column(db.Text())
    logo_id = db.Column(db.Integer, default=0)

    # sort number
    sort_order = db.Column(db.SmallInteger, default=1)
    # status: 1, default; 2, online
    status = db.Column(db.SmallInteger, default=1)
    # whether recommend
    is_recommended = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)


    def __repr__(self):
        return '<Brand %r>' % self.name

    @property
    def logo(self):
        """logo asset info"""
        return Asset.query.get(self.logo_id) if self.logo_id else None


class Category(db.Model):
    """产品类别"""

    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    name = db.Column(db.String(32), index=True)
    pid = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.SmallInteger, default=0)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    __table_args__ = (
        db.UniqueConstraint('master_uid', 'name', name='uix_master_uid_name'),
        db.Index('ix_master_uid_pid', 'master_uid', 'pid')
    )

    # category and product => N to N
    products = db.relationship(
        'Product', secondary=product_category_table, backref='categories'
    )

    category_paths = db.relationship(
        'CategoryPath', backref='category', cascade='delete'
    )

    @classmethod
    def always_category(cls, path=0, page=1, per_page=20, uid=0):
        """get category tree"""
        sql = "SELECT cp.category_id, group_concat(c.name ORDER BY cp.level SEPARATOR '&nbsp;&nbsp;&gt;&nbsp;&nbsp;') AS name, c2.id, c2.sort_order, c2.status FROM categories_paths AS cp"
        sql += " LEFT JOIN categories c ON (cp.path_id=c.id)"
        sql += " LEFT JOIN categories AS c2 ON (cp.category_id=c2.id)"

        sql += " WHERE c2.master_uid=%d" % uid
        sql += " GROUP BY cp.category_id"
        sql += " ORDER BY cp.category_id ASC"

        if page == 1:
            offset = 0
        else:
            offset = (page - 1) * per_page

        sql += ' LIMIT %d, %d' % (offset, per_page)

        return db.engine.execute(text(sql))


    @classmethod
    def repair_categories(cls, pid=0):
        """repair category path"""

        categories = Category.query.filter_by(pid=pid).all()

        for cate in categories:
            db.engine.execute("DELETE FROM `categories_paths` WHERE category_id=%d" % cate.id)

            level = 0

            categories_paths = CategoryPath.query.filter_by(category_id=pid).order_by(
                CategoryPath.level.asc()).all()
            for cp in categories_paths:
                cp = CategoryPath(category_id=cate.id, path_id=cp.path_id, level=level)
                db.session.add(cp)

                level += 1

            db.engine.execute(
                'REPLACE INTO `categories_paths` SET category_id=%d, path_id=%d, level=%d' % (cate.id, cate.id, level))

            db.session.commit()

            Category.repair_categories(cate.id)


    def __repr__(self):
        return '<Category %r>' % self.name


class CategoryPath(db.Model):
    """类别路径"""

    __tablename__ = 'categories_paths'

    __table_args__ = (
        db.PrimaryKeyConstraint('category_id', 'path_id'),
    )

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    path_id = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=0)


    def __repr__(self):
        return '<CategoryPath %r>' % self.category_id


# 添加监听事件, 实现触发器
event.listen(ProductSku, 'after_insert', SupplyStats.on_sync_change)
event.listen(Purchase, 'after_insert', SupplyStats.on_sync_change)