"""add serial_no subscribe_services table

Revision ID: e4306c6fc286
Revises: 9e11f89d3025
Create Date: 2018-04-24 18:56:22.513171

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4306c6fc286'
down_revision = '9e11f89d3025'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_product_statistics_master_uid', table_name='product_statistics')
    op.create_index(op.f('ix_product_statistics_master_uid'), 'product_statistics', ['master_uid'], unique=False)
    op.add_column('subscribe_services', sa.Column('service_serial_no', sa.String(length=10), nullable=True))
    op.create_index(op.f('ix_subscribe_services_service_serial_no'), 'subscribe_services', ['service_serial_no'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_subscribe_services_service_serial_no'), table_name='subscribe_services')
    op.drop_column('subscribe_services', 'service_serial_no')
    op.drop_index(op.f('ix_product_statistics_master_uid'), table_name='product_statistics')
    op.create_index('ix_product_statistics_master_uid', 'product_statistics', ['master_uid', 'sku_id', 'time', 'store_id'], unique=False)
    # ### end Alembic commands ###
