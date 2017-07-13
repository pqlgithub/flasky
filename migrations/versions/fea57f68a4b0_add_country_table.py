"""add country table

Revision ID: fea57f68a4b0
Revises: 99f39e0e6de0
Create Date: 2017-07-11 11:17:45.748035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fea57f68a4b0'
down_revision = '99f39e0e6de0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('countries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cn_name', sa.String(length=128), nullable=False),
    sa.Column('en_name', sa.String(length=128), nullable=False),
    sa.Column('code', sa.String(length=16), nullable=False),
    sa.Column('code2', sa.String(length=16), nullable=True),
    sa.Column('status', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_countries_cn_name'), 'countries', ['cn_name'], unique=False)
    op.create_index(op.f('ix_countries_code'), 'countries', ['code'], unique=False)
    op.create_index(op.f('ix_countries_en_name'), 'countries', ['en_name'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_countries_en_name'), table_name='countries')
    op.drop_index(op.f('ix_countries_code'), table_name='countries')
    op.drop_index(op.f('ix_countries_cn_name'), table_name='countries')
    op.drop_table('countries')
    # ### end Alembic commands ###
