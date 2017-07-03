"""remove warehouse serial_number table

Revision ID: eb0bd00a8499
Revises: c0edc3b2fcac
Create Date: 2017-06-14 00:30:01.675858

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'eb0bd00a8499'
down_revision = 'c0edc3b2fcac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('serial_number', table_name='warehouse_shelves')
    op.drop_column('warehouse_shelves', 'serial_number')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('warehouse_shelves', sa.Column('serial_number', mysql.VARCHAR(length=32), nullable=False))
    op.create_index('serial_number', 'warehouse_shelves', ['serial_number'], unique=True)
    # ### end Alembic commands ###
