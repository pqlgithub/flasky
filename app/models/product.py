# -*- coding: utf-8 -*-
import re
from sqlalchemy import text, event
from sqlalchemy.sql import func
from bs4 import BeautifulSoup, element
from flask import current_app, abort
from flask_babelex import gettext, lazy_gettext
from jieba.analyse.analyzer import ChineseAnalyzer
from app import db
from .asset import Asset
from ..utils import timestamp, gen_serial_no
from ..constant import DEFAULT_IMAGES, DEFAULT_REGIONS
from app.helpers import MixGenId, FxFilter


__all__ = [
    'Product',
    'ProductSku',
    'ProductStock',
    'ProductContent',
    'ProductDistribution',
    'CustomsDeclaration',
    'Brand',
    'Supplier',
    'SupplyStats',
    'Category',
    'CategoryPath',
    'Wishlist',
    'DANGEROUS_GOODS_TYPES',
    'BUSINESS_MODE'
]


# 海关危险品
DANGEROUS_GOODS_TYPES = [
    ('N', lazy_gettext('No')),
    ('D', lazy_gettext('Electricity')),  # 含电
    ('Y', lazy_gettext('Liquid')),  # 液体
    ('F', lazy_gettext('Powder'))  # 粉末
]

# 供应商合作方式
BUSINESS_MODE = [
    ('C', gettext('Direct purchasing'), lazy_gettext('Direct purchasing')),  # 直采
    ('D', gettext('Proxy'), lazy_gettext('Proxy')),  # 代理
    ('Q', gettext('Exclusive'), lazy_gettext('Exclusive'))  # 独家
]

# 产品的状态
PRODUCT_STATUS = [
    (True, lazy_gettext('In Sale'), 'success'),
    (False, lazy_gettext('Off Sale'), 'danger')
]

# product and category => N to N
product_category_table = db.Table('categories_products',
                                  db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
                                  db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
                                  )


class Product(db.Model):
    """产品基本信息"""

    __tablename__ = 'products'

    __searchable__ = ['serial_no', 'name', 'description', 'all_sku']
    __analyzer__ = ChineseAnalyzer()
    
    id = db.Column(db.Integer, primary_key=True)
    # 产品编号
    serial_no = db.Column(db.String(12), unique=True, index=True, nullable=False)
    master_uid = db.Column(db.Integer, index=True, default=0)

    # 所属品牌
    brand_id = db.Column(db.Integer, default=0)
    # 所属供应商
    supplier_id = db.Column(db.Integer, default=0)
    
    name = db.Column(db.String(128), nullable=False)
    cover_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    # commodity codes
    id_code = db.Column(db.String(16), nullable=True)
    # 区域
    region_id = db.Column(db.SmallInteger, default=1)
    # 采购价
    cost_price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 零售价
    price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 促销价
    sale_price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 总库存数, 设置sku库存数时自动累加
    total_stock = db.Column(db.Integer, default=0)

    # 用于出库称重和利润计算
    s_weight = db.Column(db.Numeric(precision=10, scale=2), default=0)
    s_length = db.Column(db.Numeric(precision=10, scale=2), default=0)
    s_width = db.Column(db.Numeric(precision=10, scale=2), default=0)
    s_height = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 来源URL
    from_url = db.Column(db.String(255), nullable=True)
    type = db.Column(db.SmallInteger, default=1)
    status = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text())
    # 是否推荐
    sticked = db.Column(db.Boolean, default=False)
    # 推荐语或优势亮点
    features = db.Column(db.String(100))
    # 销售总数量
    sale_count = db.Column(db.Integer, default=0)
    # 是否为分销商品
    is_distributed = db.Column(db.Boolean, default=False)
    # 分销商数量
    distributer_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    published_at = db.Column(db.Integer, default=0)

    # product and sku => 1 to N
    skus = db.relationship(
        'ProductSku', backref='product', lazy='dynamic', cascade='delete'
    )

    # product and content => 1 to 1
    details = db.relationship(
        'ProductContent', backref='product', uselist=False, cascade='delete'
    )
    
    # product and customs declaration => 1 to 1
    declaration = db.relationship(
        'CustomsDeclaration', backref='product', uselist=False, cascade='delete'
    )

    @property
    def brand(self):
        """品牌信息"""
        return Brand.query.get(self.brand_id) if self.brand_id else None

    @property
    def supplier(self):
        """供应商信息"""
        return Supplier.query.get(self.supplier_id) if self.supplier_id else None

    @property
    def brand_name(self):
        """品牌名称，用于索引"""
        return self.brand.name if self.brand else None

    @property
    def supplier_name(self):
        """供应商信息，用于索引"""
        if self.supplier:
            return '{} {}'.format(self.supplier.short_name, self.supplier.full_name)

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
    def region_label(self):
        for r in DEFAULT_REGIONS:
            if r['id'] == self.region_id:
                return r

    @property
    def cover(self):
        """cover asset info"""
        if self.cover_id:
            asset = Asset.query.get(self.cover_id)
            if asset is not None:
                return asset

        return Asset.default_logo()

    @property
    def stock_count(self):
        """product stock count"""
        row = self.skus.with_entities(func.sum(ProductSku.stock_quantity).label('total_stock')).one()
        return row[0] if row else 0

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
        if Product.query.filter_by(serial_no=serial_no).first() is None:
            return serial_no
        while True:
            new_serial_no = MixGenId.gen_product_sku()
            if Product.query.filter_by(serial_no=new_serial_no).first() is None:
                break
        return new_serial_no

    @staticmethod
    def on_before_change(mapper, connection, target):
        """插入或更新前事件"""
        # 为空时，默认为0
        if not target.sale_price:
            target.sale_price = 0
        
    @classmethod
    def always_category(cls, path=0, page=1, per_page=20, uid=0):
        """get category tree"""
        sql = "SELECT cp.category_id, group_concat(c.name ORDER BY cp.level SEPARATOR '&nbsp;&nbsp;&gt;&nbsp;&nbsp;') AS name, c2.id, c2.sort_order, c2.status FROM categories_paths AS cp"
        sql += " LEFT JOIN categories c ON (cp.path_id=c.id)"
        sql += " LEFT JOIN categories AS c2 ON (cp.category_id=c2.id)"
    
        sql += " WHERE c2.master_uid=%d" % uid
        sql += " GROUP BY cp.category_id"
        sql += " ORDER BY cp.category_id ASC, c2.sort_order ASC"
    
        if page == 1:
            offset = 0
        else:
            offset = (page - 1) * per_page
    
        sql += ' LIMIT %d, %d' % (offset, per_page)
    
        return db.engine.execute(text(sql))

    @staticmethod
    def create(data):
        """创建新产品"""
        product = Product()
        product.from_json(data, partial_update=True)

        return product

    def from_json(self, data, partial_update=True):
        """从请求json里导入数据"""
        fields = ['master_uid', 'serial_no', 'brand_id', 'supplier_id', 'name', 'cover_id', 'id_code', 'cost_price',
                  'price', 'sale_price', 's_weight', 's_length', 's_width', 's_height', 'type', 'status', 'description',
                  'features', 'sticked']

        for field in fields:
            try:
                setattr(self, field, data[field])
            except KeyError as err:
                current_app.logger.warn('Product set error: %s' % str(err))
                if not partial_update:
                    abort(400)
    
    def to_json(self, filter_fields=[]):
        """资源和JSON的序列化转换"""
        json_product = {
            'rid': self.serial_no,
            'name': self.name,
            'cover': self.cover.view_url,
            'id_code': self.id_code,
            'cost_price': str(self.cost_price),
            'sale_price': self.sale_price,
            'price': self.price,
            'features': self.features,
            'description': self.description,
            'sticked': self.sticked,
            's_weight': self.s_weight,
            's_length': self.s_length,
            's_width': self.s_width,
            's_height': self.s_height,
            'stock_count': self.stock_count
        }

        # 过滤数据
        if filter_fields:
            json_product = FxFilter.product_data(json_product, filter_fields)

        return json_product

    def __repr__(self):
        return '<Product %r>' % self.name


class ProductSku(db.Model):
    """产品的SKU"""

    __tablename__ = 'product_skus'

    __searchable__ = ['serial_no', 'product_name', 'supplier_name']
    __analyzer__ = ChineseAnalyzer()

    id = db.Column(db.Integer, primary_key=True)

    master_uid = db.Column(db.Integer, index=True, default=0)
    supplier_id = db.Column(db.Integer, default=0)

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    # 产品编号sku
    serial_no = db.Column(db.String(12), unique=True, index=True, nullable=False)
    cover_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    # 69码 commodity codes
    id_code = db.Column(db.String(16), nullable=True)
    # 型号
    s_model = db.Column(db.String(64), nullable=False)
    # 颜色
    s_color = db.Column(db.String(32), nullable=True)
    # 重量
    s_weight = db.Column(db.Numeric(precision=10, scale=2), default=0.00)
    # 区域
    region_id = db.Column(db.SmallInteger, default=1)
    # 采购价
    cost_price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 零售价
    price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 促销价
    sale_price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 库存数
    stock_quantity = db.Column(db.Integer, default=0)
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
        return self.product.name if self.product else ''

    @property
    def supplier(self):
        """供应商信息"""
        return Supplier.query.get(self.supplier_id) if self.supplier_id else None

    @property
    def supplier_name(self):
        """供应商信息，用于索引"""
        if self.supplier:
            return '{} {}'.format(self.supplier.short_name, self.supplier.full_name)
        return None

    @property
    def region_label(self):
        for r in DEFAULT_REGIONS:
            if r['id'] == self.region_id:
                return r
    
    @property
    def cover(self):
        """cover asset info"""
        return Asset.query.get(self.cover_id) if self.cover_id else Asset.default_logo()
    
    @property
    def mode(self):
        """型号"""
        mode_str = ''
        if self.s_model:
            mode_str += self.s_model + ' '
        
        if self.s_color:
            mode_str += self.s_color
        
        return mode_str
    
    @property
    def stock_count(self):
        """product sku stock count"""
        return self.stock_quantity

    @property
    def no_arrival_count(self):
        """product sku no arrival count"""
        return ProductStock.stock_count_of_no_arrival(self.id)
    
    @staticmethod
    def validate_unique_id_code(id_code, master_uid=0):
        """验证id_code是否唯一"""
        sql = "SELECT s.id,s.id_code FROM `product_skus` AS s LEFT JOIN `products` AS p ON s.product_id=p.id"
        sql += " WHERE s.id_code=%s" % id_code

        if master_uid:
            sql += " AND s.master_uid=%d" % master_uid

        result = db.engine.execute(text(sql))
        return result.fetchall()

    @staticmethod
    def make_unique_serial_no(serial_no):
        if ProductSku.query.filter_by(serial_no=serial_no).first() is None:
            return serial_no
        while True:
            new_serial_no = MixGenId.gen_product_sku()
            if ProductSku.query.filter_by(serial_no=new_serial_no).first() is None:
                break
        return new_serial_no

    def to_json(self, filter_fields=()):
        """资源和JSON的序列化转换"""
        json_sku = {
            'product_name': self.product_name,
            'rid': self.serial_no,
            'mode': self.mode,
            'id_code': self.id_code,
            's_model': self.s_model,
            's_color': self.s_color,
            'cover': self.cover.view_url,
            'cost_price': str(self.cost_price),
            'price': str(self.price),
            'sale_price': str(self.sale_price),
            's_weight': str(self.s_weight),
            'stock_count': self.stock_count
        }

        # 过滤数据
        if filter_fields:
            json_sku = FxFilter.product_data(json_sku, filter_fields)

        return json_sku

    def __repr__(self):
        return '<ProductSku %r>' % self.serial_no


class ProductContent(db.Model):
    """产品内容详情"""

    __tablename__ = 'product_contents'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    # 附件图片列表，多个图片逗号隔开
    asset_ids = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    # 分销说明
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def images(self):
        imgs = []
        if not self.asset_ids:
            return imgs

        asset_ids = self.asset_ids.split(',')
        assets = Asset.query.filter(Asset.id.in_(asset_ids)).all()

        return [asset.to_json() for asset in assets]

    @property
    def split_content(self):
        """将移动应用拆分内容为列表"""
        content_list = []
        if not self.content:
            return content_list
        rex = re.compile('\W+')  # 匹配任意不是字母，数字，下划线，汉字的字符
        html = BeautifulSoup(self.content, 'html.parser')
        for node in html.select('p'):
            if type(node) == element.NavigableString:
                c = rex.sub('', node.string)
                if c:
                    content_list.append({
                        'rid': MixGenId.gen_digits(),
                        'type': 'text',
                        'content': c
                    })
            else:
                for child in node.children:
                    if type(child) == element.NavigableString:
                        c = rex.sub('', child.string)
                        if c:
                            content_list.append({
                                'rid': MixGenId.gen_digits(),
                                'type': 'text',
                                'content': c
                            })
                    elif type(child) == element.Tag and child.name == 'img':
                        content_list.append({
                            'rid': MixGenId.gen_digits(),
                            'type': 'image',
                            'content': child['src']
                        })

        return content_list

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_obj = {
            'images': self.images,
            'tags': self.tags,
            'content': self.split_content
        }
        return json_obj

    def __repr__(self):
        return '<ProductContent {}>'.format(self.product_id)


class ProductDistribution(db.Model):
    """商品分销信息"""

    __tablename__ = 'product_distribution'

    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_serial_no = db.Column(db.String(12), index=True, nullable=False)

    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'), index=True)
    sku_serial_no = db.Column(db.String(12), index=True, nullable=False)
    # 分销价
    distribute_price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    # 建议零售价
    suggested_min_price = db.Column(db.Numeric(precision=10, scale=2), default=0)
    suggested_max_price = db.Column(db.Numeric(precision=10, scale=2), default=0)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    def __repr__(self):
        return '<ProductDistribution %r>' % self.id


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
        total_quantity = ProductStock.query.filter_by(product_sku_id=sku_id)\
            .with_entities(func.sum(ProductStock.current_count)).one()

        return total_quantity[0] if (total_quantity and total_quantity[0] is not None) else 0

    @staticmethod
    def stock_count_of_no_arrival(sku_id):
        """未到货库存数"""
        sql = "SELECT SUM(s.quantity) FROM `purchase_product` AS s LEFT JOIN `purchases` AS p ON s.purchase_id=p.id"
        sql += " WHERE s.product_sku_id=%d AND p.status=5" % sku_id

        result = db.engine.execute(sql).fetchone()

        return result[0] if result[0] is not None else 0

    @staticmethod
    def hook_after_change(mapper, connection, target):
        """插入或更新后事件"""
        from app.tasks import sync_sku_stock
        # run the task
        sync_sku_stock.apply_async(args=[target.product_sku_id], countdown=3)

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

    def to_json(self):
        """资源和JSON的序列化转换"""
        return {
            c.name: getattr(self, c.name, None) for c in self.__table__.columns
        }

    def __repr__(self):
        return '<Supplier %r>' % self.full_name


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

    def __repr__(self):
        return '<SupplyStats %r>' % self.supplier_id


class Brand(db.Model):
    """品牌信息"""

    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    sn = db.Column(db.String(9), unique=True, index=True, nullable=True)
    
    master_uid = db.Column(db.Integer, index=True, default=0)
    supplier_id = db.Column(db.Integer, default=0)
    
    name = db.Column(db.String(64), index=True)
    features = db.Column(db.String(100))
    description = db.Column(db.Text())
    
    logo_id = db.Column(db.Integer, default=0)
    banner_id = db.Column(db.Integer, default=0)
    
    # sort number
    sort_order = db.Column(db.SmallInteger, default=1)
    # status: 1, default; 2, online
    status = db.Column(db.SmallInteger, default=1)
    # whether recommend
    is_recommended = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    @property
    def supplier(self):
        """供应商信息"""
        return Supplier.query.get(self.supplier_id) if self.supplier_id else None

    @property
    def logo(self):
        """logo asset info"""
        if self.logo_id:
            asset = Asset.query.get(self.logo_id)
            if asset:
                return asset
        return Asset.default_logo()

    @property
    def banner(self):
        """brand asset info"""
        return Asset.query.get(self.banner_id) if self.banner_id else Asset.default_banner()

    @staticmethod
    def make_unique_sn():
        """生成品牌编号"""
        sn = MixGenId.gen_brand_sn()
        if Brand.query.filter_by(sn=sn).first() is None:
            return sn
        
        while True:
            new_sn = MixGenId.gen_brand_sn()
            if Brand.query.filter_by(sn=new_sn).first() is None:
                break
        return new_sn

    @staticmethod
    def on_before_insert(mapper, connection, target):
        # 自动生成用户编号
        target.sn = Brand.make_unique_sn()

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_brand = {
            'rid': self.sn,
            'name': self.name,
            'logo': self.logo.view_url,
            'banner': self.banner.view_url,
            'features': self.features,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_recommended': self.is_recommended,
            'status': self.status
        }
        return json_brand

    @staticmethod
    def from_json(json_brand):
        """从json格式数据创建，对API支持"""
        # todo: 数据验证
        return Brand(
            supplier_id=json_brand.get('supplier_id'),
            name=json_brand.get('name'),
            features=json_brand.get('features'),
            is_recommended=json_brand.get('is_recommended'),
            sort_order=json_brand.get('sort_order'),
            description=json_brand.get('description')
        )
    
    def __repr__(self):
        return '<Brand %r>' % self.name


class Category(db.Model):
    """产品类别"""

    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    name = db.Column(db.String(32), index=True)
    pid = db.Column(db.Integer, default=0)
    cover_id = db.Column(db.Integer, default=0)
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
        'Product', secondary=product_category_table, backref=db.backref('categories', lazy='select'), lazy='dynamic'
    )
    
    category_paths = db.relationship(
        'CategoryPath', backref='category', cascade='delete'
    )

    @property
    def cover(self):
        """cover asset info"""
        return Asset.query.get(self.cover_id) if self.cover_id else Asset.default_logo()
    
    @classmethod
    def always_category(cls, path=0, page=1, per_page=20, uid=0):
        """get category tree"""
        sql = "SELECT cp.category_id, group_concat(c.name ORDER BY cp.level SEPARATOR '&nbsp;&nbsp;&gt;&nbsp;&nbsp;') AS name, c2.id, c2.sort_order, c2.status FROM categories_paths AS cp"
        sql += " LEFT JOIN categories c ON (cp.path_id=c.id)"
        sql += " LEFT JOIN categories AS c2 ON (cp.category_id=c2.id)"

        sql += " WHERE c2.master_uid=%d" % uid
        sql += " GROUP BY cp.category_id"
        sql += " ORDER BY cp.category_id ASC, c2.sort_order ASC"

        if page == 1:
            offset = 0
        else:
            offset = (page - 1) * per_page

        sql += ' LIMIT %d, %d' % (offset, per_page)

        return db.engine.execute(text(sql))

    @classmethod
    def repair_categories(cls, master_uid, pid=0):
        """repair category path"""

        categories = Category.query.filter_by(master_uid=master_uid, pid=pid).all()

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

            Category.repair_categories(master_uid, cate.id)
    
    def to_json(self):
        """资源和JSON的序列化转换"""
        json_category = {
            'id': self.id,
            'name': self.name,
            'pid': self.pid,
            'cover': self.cover.view_url,
            'sort_order': self.sort_order,
            'description': self.description,
            'status': self.status
        }
        return json_category
    
    @staticmethod
    def from_json(json_category):
        """从json格式数据创建，对API支持"""
        # todo: 数据验证
        return Category(
            name=json_category.get('name'),
            sort_order=json_category.get('sort_order'),
            description=json_category.get('description')
        )
    
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


class Wishlist(db.Model):
    """愿望清单"""
    
    __tablename__ = 'wishlist'
    
    id = db.Column(db.Integer, primary_key=True)
    master_uid = db.Column(db.Integer, index=True, default=0)
    
    user_id = db.Column(db.Integer, default=0)
    product_rid = db.Column(db.String(12), nullable=False)
    
    created_at = db.Column(db.Integer, default=timestamp)
    
    def __repr__(self):
        return '<Wishlist {}>'.format(self.id)


# 添加监听事件, 实现触发器
event.listen(Product, 'before_insert', Product.on_before_change)
event.listen(Product, 'before_update', Product.on_before_change)
# 监听Brand事件
event.listen(Brand, 'before_insert', Brand.on_before_insert)
event.listen(ProductStock, 'after_insert', ProductStock.hook_after_change)
event.listen(ProductStock, 'after_update', ProductStock.hook_after_change)
