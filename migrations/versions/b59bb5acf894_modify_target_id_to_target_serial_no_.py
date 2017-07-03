"""modify target_id to target_serial_no for in_warehouse/out_warehouse table

Revision ID: b59bb5acf894
Revises: 877147b8e706
Create Date: 2017-06-29 23:57:00.906688

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b59bb5acf894'
down_revision = '877147b8e706'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('warehouse_in_list', sa.Column('target_serial_no', sa.String(length=20), nullable=False))
    op.create_index('ix_target_serial_type', 'warehouse_in_list', ['target_serial_no', 'target_type'], unique=False)
    op.create_index(op.f('ix_warehouse_in_list_target_serial_no'), 'warehouse_in_list', ['target_serial_no'], unique=False)
    op.drop_column('warehouse_in_list', 'target_id')
    op.add_column('warehouse_out_list', sa.Column('target_serial_no', sa.String(length=20), nullable=False))
    op.create_index('ix_target_serial_type', 'warehouse_out_list', ['target_serial_no', 'target_type'], unique=False)
    op.create_index(op.f('ix_warehouse_out_list_target_serial_no'), 'warehouse_out_list', ['target_serial_no'], unique=False)
    op.drop_column('warehouse_out_list', 'target_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('warehouse_out_list', sa.Column('target_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_warehouse_out_list_target_serial_no'), table_name='warehouse_out_list')
    op.drop_index('ix_target_serial_type', table_name='warehouse_out_list')
    op.drop_column('warehouse_out_list', 'target_serial_no')
    op.add_column('warehouse_in_list', sa.Column('target_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_warehouse_in_list_target_serial_no'), table_name='warehouse_in_list')
    op.drop_index('ix_target_serial_type', table_name='warehouse_in_list')
    op.drop_column('warehouse_in_list', 'target_serial_no')
    # ### end Alembic commands ###
