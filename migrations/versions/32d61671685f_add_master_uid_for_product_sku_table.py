"""add master_uid for product_sku table

Revision ID: 32d61671685f
Revises: 0787afd55040
Create Date: 2017-07-09 16:52:56.495280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32d61671685f'
down_revision = '0787afd55040'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_skus', sa.Column('master_uid', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_product_skus_master_uid'), 'product_skus', ['master_uid'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_product_skus_master_uid'), table_name='product_skus')
    op.drop_column('product_skus', 'master_uid')
    # ### end Alembic commands ###
