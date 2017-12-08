"""add is_default for discount templet

Revision ID: c246d4c91747
Revises: 1407bf4314ee
Create Date: 2017-12-07 18:23:13.899858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c246d4c91747'
down_revision = '1407bf4314ee'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('discount_templets', sa.Column('is_default', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('discount_templets', 'is_default')
    # ### end Alembic commands ###
