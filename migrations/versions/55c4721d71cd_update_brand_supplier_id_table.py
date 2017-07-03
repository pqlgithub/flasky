"""update brand supplier_id table

Revision ID: 55c4721d71cd
Revises: 54c4bfbda7dc
Create Date: 2017-06-14 15:50:04.307588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55c4721d71cd'
down_revision = '54c4bfbda7dc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('brands', sa.Column('supplier_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'brands', 'suppliers', ['supplier_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'brands', type_='foreignkey')
    op.drop_column('brands', 'supplier_id')
    # ### end Alembic commands ###
