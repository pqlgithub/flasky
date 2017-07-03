"""modify field type for order/order_item table

Revision ID: 6e90d9978fc0
Revises: b59bb5acf894
Create Date: 2017-07-01 15:25:45.677214

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e90d9978fc0'
down_revision = 'b59bb5acf894'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order_items', sa.Column('order_serial_no', sa.String(length=20), nullable=False))
    op.create_index(op.f('ix_order_items_order_serial_no'), 'order_items', ['order_serial_no'], unique=False)
    op.create_index(op.f('ix_order_items_sku_serial_no'), 'order_items', ['sku_serial_no'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_order_items_sku_serial_no'), table_name='order_items')
    op.drop_index(op.f('ix_order_items_order_serial_no'), table_name='order_items')
    op.drop_column('order_items', 'order_serial_no')
    # ### end Alembic commands ###
