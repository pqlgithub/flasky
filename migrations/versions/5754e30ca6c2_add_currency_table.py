"""add currency table

Revision ID: 5754e30ca6c2
Revises: 80c78fffa8ec
Create Date: 2017-08-14 00:17:15.756227

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5754e30ca6c2'
down_revision = '80c78fffa8ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('currencies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=32), nullable=False),
    sa.Column('code', sa.String(length=3), nullable=False),
    sa.Column('symbol_left', sa.String(length=12), nullable=True),
    sa.Column('symbol_right', sa.String(length=12), nullable=True),
    sa.Column('decimal_place', sa.String(length=1), nullable=False),
    sa.Column('value', sa.Float(precision=15, asdecimal=8), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('updated_at', sa.Integer(), nullable=True),
    sa.Column('last_updated', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('title')
    )
    op.add_column('products', sa.Column('currency_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'products', 'currencies', ['currency_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'products', type_='foreignkey')
    op.drop_column('products', 'currency_id')
    op.drop_table('currencies')
    # ### end Alembic commands ###
