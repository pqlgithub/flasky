"""modify field type for order/order_item table

Revision ID: 4c39dbc3fe23
Revises: 15cb1311e71d
Create Date: 2017-07-01 15:30:25.564885

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c39dbc3fe23'
down_revision = '15cb1311e71d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('serial_no', sa.String(length=20), nullable=False))
    op.create_index(op.f('ix_orders_serial_no'), 'orders', ['serial_no'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_orders_serial_no'), table_name='orders')
    op.drop_column('orders', 'serial_no')
    # ### end Alembic commands ###
