"""add ship mode orders table

Revision ID: ad97ff648d84
Revises: 1aee3df335f8
Create Date: 2018-04-09 14:41:59.015556

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad97ff648d84'
down_revision = '1aee3df335f8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('ship_mode', sa.SmallInteger(), nullable=True))
    op.drop_constraint('orders_ibfk_4', 'orders', type_='foreignkey')
    op.drop_index('ix_product_statistics_master_uid', table_name='product_statistics')
    op.create_index(op.f('ix_product_statistics_master_uid'), 'product_statistics', ['master_uid'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_product_statistics_master_uid'), table_name='product_statistics')
    op.create_index('ix_product_statistics_master_uid', 'product_statistics', ['master_uid', 'sku_id', 'time', 'store_id'], unique=False)
    op.create_foreign_key('orders_ibfk_4', 'orders', 'addresses', ['address_id'], ['id'])
    op.drop_column('orders', 'ship_mode')
    # ### end Alembic commands ###
