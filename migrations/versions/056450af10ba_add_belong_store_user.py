"""add belong store user

Revision ID: 056450af10ba
Revises: ad97ff648d84
Create Date: 2018-04-11 13:48:03.712469

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '056450af10ba'
down_revision = 'ad97ff648d84'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_product_statistics_master_uid', table_name='product_statistics')
    op.create_index(op.f('ix_product_statistics_master_uid'), 'product_statistics', ['master_uid', 'sku_id', 'time', 'store_id'], unique=False)
    op.add_column('users', sa.Column('belong_store', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'belong_store')
    op.drop_index(op.f('ix_product_statistics_master_uid'), table_name='product_statistics')
    op.create_index('ix_product_statistics_master_uid', 'product_statistics', ['master_uid'], unique=False)
    # ### end Alembic commands ###
