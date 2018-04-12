"""remove currency_id warehouse table

Revision ID: 28b6f51b3f61
Revises: f533e982f26b
Create Date: 2018-04-12 21:25:30.232130

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '28b6f51b3f61'
down_revision = 'f533e982f26b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_product_statistics_master_uid', table_name='product_statistics')
    op.create_index(op.f('ix_product_statistics_master_uid'), 'product_statistics', ['master_uid'], unique=False)
    op.drop_constraint('warehouses_ibfk_1', 'warehouses', type_='foreignkey')
    op.drop_column('warehouses', 'currency_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('warehouses', sa.Column('currency_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key('warehouses_ibfk_1', 'warehouses', 'currencies', ['currency_id'], ['id'])
    op.drop_index(op.f('ix_product_statistics_master_uid'), table_name='product_statistics')
    op.create_index('ix_product_statistics_master_uid', 'product_statistics', ['master_uid', 'sku_id', 'time', 'store_id'], unique=False)
    # ### end Alembic commands ###
