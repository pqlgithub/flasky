"""add master_uid warehouse_id banner

Revision ID: e96f068bc205
Revises: b88684c40b90
Create Date: 2018-01-02 21:00:34.144740

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e96f068bc205'
down_revision = 'b88684c40b90'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order_items', sa.Column('master_uid', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('warehouse_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_order_items_master_uid'), 'order_items', ['master_uid'], unique=False)
    op.create_foreign_key(None, 'order_items', 'warehouses', ['warehouse_id'], ['id'])
    op.drop_constraint('orders_ibfk_2', 'orders', type_='foreignkey')
    op.drop_column('orders', 'warehouse_id')
    op.drop_index('ix_product_statistics_master_uid', table_name='product_statistics')
    op.create_index(op.f('ix_product_statistics_master_uid'), 'product_statistics', ['master_uid', 'sku_id', 'time', 'store_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_product_statistics_master_uid'), table_name='product_statistics')
    op.create_index('ix_product_statistics_master_uid', 'product_statistics', ['master_uid'], unique=False)
    op.add_column('orders', sa.Column('warehouse_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key('orders_ibfk_2', 'orders', 'warehouses', ['warehouse_id'], ['id'])
    op.drop_constraint(None, 'order_items', type_='foreignkey')
    op.drop_index(op.f('ix_order_items_master_uid'), table_name='order_items')
    op.drop_column('order_items', 'warehouse_id')
    op.drop_column('order_items', 'master_uid')
    # ### end Alembic commands ###
