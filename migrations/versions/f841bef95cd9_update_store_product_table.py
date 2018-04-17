"""update store product table

Revision ID: f841bef95cd9
Revises: ad3da7c94561
Create Date: 2018-04-17 13:42:26.458358

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f841bef95cd9'
down_revision = 'ad3da7c94561'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('store_products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('master_uid', sa.Integer(), nullable=True),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('store_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('store_product')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('store_product',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('master_uid', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('product_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('store_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='store_product_ibfk_1'),
    sa.ForeignKeyConstraint(['store_id'], ['stores.id'], name='store_product_ibfk_2'),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.drop_table('store_products')
    # ### end Alembic commands ###
