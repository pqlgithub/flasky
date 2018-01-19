"""add cover_id category

Revision ID: 85abe55d61df
Revises: e96f068bc205
Create Date: 2018-01-07 23:59:43.634536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85abe55d61df'
down_revision = 'e96f068bc205'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('categories', sa.Column('cover_id', sa.Integer(), nullable=True))
    op.drop_index('ix_product_statistics_master_uid', table_name='product_statistics')
    op.create_index(op.f('ix_product_statistics_master_uid'), 'product_statistics', ['master_uid'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_product_statistics_master_uid'), table_name='product_statistics')
    op.create_index('ix_product_statistics_master_uid', 'product_statistics', ['master_uid', 'sku_id', 'time', 'store_id'], unique=False)
    op.drop_column('categories', 'cover_id')
    # ### end Alembic commands ###
