"""update supplier table

Revision ID: 9c06ef731b9c
Revises: 2a80487c151d
Create Date: 2017-06-14 16:42:11.109761

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9c06ef731b9c'
down_revision = '2a80487c151d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('suppliers', sa.Column('business_scope', sa.Text(), nullable=True))
    op.add_column('suppliers', sa.Column('contact_name', sa.String(length=32), nullable=True))
    op.add_column('suppliers', sa.Column('end_date', sa.Date(), nullable=False))
    op.add_column('suppliers', sa.Column('name', sa.String(length=10), nullable=False))
    op.add_column('suppliers', sa.Column('remark', sa.String(length=255), nullable=True))
    op.add_column('suppliers', sa.Column('start_date', sa.Date(), nullable=False))
    op.add_column('suppliers', sa.Column('type', sa.String(length=1), nullable=True))
    op.alter_column('suppliers', 'full_name',
               existing_type=mysql.VARCHAR(length=50),
               nullable=False)
    op.create_index(op.f('ix_suppliers_type'), 'suppliers', ['type'], unique=False)
    op.create_unique_constraint(None, 'suppliers', ['name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'suppliers', type_='unique')
    op.drop_index(op.f('ix_suppliers_type'), table_name='suppliers')
    op.alter_column('suppliers', 'full_name',
               existing_type=mysql.VARCHAR(length=50),
               nullable=True)
    op.drop_column('suppliers', 'type')
    op.drop_column('suppliers', 'start_date')
    op.drop_column('suppliers', 'remark')
    op.drop_column('suppliers', 'name')
    op.drop_column('suppliers', 'end_date')
    op.drop_column('suppliers', 'contact_name')
    op.drop_column('suppliers', 'business_scope')
    # ### end Alembic commands ###
