"""add store_id client

Revision ID: c9d582d0e644
Revises: 85abe55d61df
Create Date: 2018-01-09 23:06:05.008857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9d582d0e644'
down_revision = '85abe55d61df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('clients', sa.Column('store_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('clients', 'store_id')
    # ### end Alembic commands ###
