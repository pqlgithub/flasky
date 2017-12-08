"""add statistics migration

Revision ID: 620c713140b6
Revises: cba4bc28cc67
Create Date: 2017-12-04 14:28:46.539942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '620c713140b6'
down_revision = 'cba4bc28cc67'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_target_id_type', table_name='warehouse_in_list')
    op.drop_index('uix_target_id_type', table_name='warehouse_in_list')
    op.drop_index('ix_target_id_type', table_name='warehouse_out_list')
    op.drop_index('uix_target_id_type', table_name='warehouse_out_list')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('uix_target_id_type', 'warehouse_out_list', ['target_type'], unique=True)
    op.create_index('ix_target_id_type', 'warehouse_out_list', ['target_type'], unique=False)
    op.create_index('uix_target_id_type', 'warehouse_in_list', ['target_type'], unique=True)
    op.create_index('ix_target_id_type', 'warehouse_in_list', ['target_type'], unique=False)
    # ### end Alembic commands ###
