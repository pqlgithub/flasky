# -*- coding: utf-8 -*-
from sqlalchemy import text
from app import db, uploader
from ..utils import timestamp, gen_serial_no
from .asset import Asset

__all__ = [
    'Product',
    'ProductSku',
    'ProductStock',
    'CustomsDeclaration',
    'Brand',
    'Supplier',
    'Category',
    'CategoryPath'
]


# 海关危险品
DANGEROUS_GOODS_TYPES = [
    ('N', '无'),
    ('D', '含电'),
    ('Y', '液体'),
    ('F', '粉末')
]

# 供应商合作方式
BUSINESS_MODE = [
    ('C', '采销'),
    ('D', '代销'),
    ('Q', '独家')
]

# product and category => N to N
product_category_table = db.Table('categories_products',
                    db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
                    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
                )


class Product(db.Model):
    """产品信息"""

    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    # 产品编号
    serial_no = db.Column(db.String(12), unique=True, index=True, nullable=False)
    master_uid = db.Column(db.Integer, index=True, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))

    name = db.Column(db.String(128), nullable=False)
    cover_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    # 识别码
    id_code = db.Column(db.String(16), nullable=True)
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
    updated_at = db.Column(db.Integer, default=timestamp)

    # product and sku => 1 to N
    skus = db.relationship(
        'ProductSku', backref='product', lazy='dynamic'
    )

    # product and customs declaration => 1 to 1
    declaration = db.relationship(
        'CustomsDeclaration', backref='product', uselist=False
    )

    @property
    def cover(self):
        """cover asset info"""
        return Asset.query.get(self.cover_id) if self.cover_id else None

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
    id = db.Column(db.Integer, primary_key=True)
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
    updated_at = db.Column(db.Integer, default=timestamp)

    # sku and stock => 1 to N
    stocks = db.relationship(
        'ProductStock', backref='product_sku', lazy='dynamic'
    )

    @property
    def cover(self):
        """cover asset info"""
        return Asset.query.get(self.cover_id) if self.cover_id else None

    def to_json(self):
        """资源和JSON的序列化转换"""
        json_asset = {
            'id': self.id,
            'serial_no': self.serial_no,
            's_model': self.s_model,
            'cover': uploader.url(self.cover.filepath),
            'cost_price': str(self.cost_price),
            's_weight': str(self.s_weight)
        }
        return json_asset

    def __repr__(self):
        return '<Product %r>' % self.serial_no


class ProductStock(db.Model):
    """产品库存数"""

    __tablename__ = 'product_stocks'
    id = db.Column(db.Integer, primary_key=True)
    product_sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'), index=True)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), index=True)
    warehouse_shelve_id = db.Column(db.Integer, db.ForeignKey('warehouse_shelves.id'))

    # 库存总数
    total_count = db.Column(db.Integer, default=0)
    # 已销售数
    saled_count = db.Column(db.Integer, default=0)

    # 库存预警设置
    min_count = db.Column(db.Integer, default=0)
    max_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp)


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
    updated_at = db.Column(db.Integer, default=timestamp)

    def __repr__(self):
        return '<Customs %r>' % self.local_name


class Supplier(db.Model):
    """供应商信息"""

    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    # master user id
    master_uid = db.Column(db.Integer, index=True, default=0)
    # 简称
    name = db.Column(db.String(10), unique=True, nullable=False)
    # 全称
    full_name = db.Column(db.String(50), unique=True, nullable=False)
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

    time_limit = db.Column(db.String(50), nullable=True)
    business_scope = db.Column(db.Text(), nullable=True)

    created_at = db.Column(db.Integer, index=True, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp)

    # supplier and brand => 1 to N
    brands = db.relationship(
        'Brand', backref='supplier', lazy='dynamic'
    )

    # supplier and product => 1 to N
    products = db.relationship(
        'Product', backref='supplier', lazy='dynamic'
    )

    # supplier and purchase => 1 to N
    purchases = db.relationship(
        'Purchase', backref='supplier', lazy='dynamic'
    )


    @property
    def desc_type(self):
        for t in BUSINESS_MODE:
            if t[0] == self.type:
                return t

    def __repr__(self):
        return '<Supplier %r>' % self.full_name



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
    updated_at = db.Column(db.Integer, default=timestamp)


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
    name = db.Column(db.String(32), unique=True, index=True)
    pid = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.SmallInteger, default=0)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # category and product => N to N
    products = db.relationship(
        'Product', secondary=product_category_table, backref='categories'
    )

    category_paths = db.relationship(
        'CategoryPath', backref='category', cascade='delete'
    )

    @classmethod
    def always_category(cls, path=0, page=1, per_page=20):
        """get category tree"""
        sql = "SELECT cp.category_id, group_concat(c.name ORDER BY cp.level SEPARATOR '&nbsp;&nbsp;&gt;&nbsp;&nbsp;') AS name, c2.id, c2.sort_order, c2.status FROM categories_paths AS cp"
        sql += " LEFT JOIN categories c ON (cp.path_id=c.id)"
        sql += " LEFT JOIN categories AS c2 ON (cp.category_id=c2.id)"

        sql += ' GROUP BY cp.category_id'
        sql += ' ORDER BY c2.sort_order ASC'

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
