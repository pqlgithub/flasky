"""add site table

Revision ID: 228245e23a1e
Revises: cdf7905cf080
Create Date: 2017-07-02 15:52:05.437828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '228245e23a1e'
down_revision = 'cdf7905cf080'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('master_uid', sa.Integer(), nullable=True),
    sa.Column('company_name', sa.String(length=50), nullable=False),
    sa.Column('company_abbr', sa.String(length=10), nullable=True),
    sa.Column('language', sa.String(length=4), nullable=True),
    sa.Column('country', sa.String(length=30), nullable=True),
    sa.Column('locale', sa.String(length=4), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('domain', sa.SmallInteger(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sites_company_name'), 'sites', ['company_name'], unique=True)
    op.create_index(op.f('ix_sites_master_uid'), 'sites', ['master_uid'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_sites_master_uid'), table_name='sites')
    op.drop_index(op.f('ix_sites_company_name'), table_name='sites')
    op.drop_table('sites')
    # ### end Alembic commands ###
