"""wx token table

Revision ID: 6aace906eedc
Revises: da22f59cfa2a
Create Date: 2018-02-22 10:50:10.415029

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6aace906eedc'
down_revision = 'da22f59cfa2a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wx_auth_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('app_id', sa.String(length=20), nullable=True),
    sa.Column('pre_auth_code', sa.String(length=100), nullable=False),
    sa.Column('expires_in', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('pre_auth_code')
    )
    op.create_index(op.f('ix_wx_auth_codes_app_id'), 'wx_auth_codes', ['app_id'], unique=False)
    op.create_table('wx_authorizer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('master_uid', sa.Integer(), nullable=True),
    sa.Column('app_id', sa.String(length=20), nullable=False),
    sa.Column('access_token', sa.String(length=200), nullable=False),
    sa.Column('refresh_token', sa.String(length=200), nullable=False),
    sa.Column('expires_in', sa.Integer(), nullable=True),
    sa.Column('func_info', sa.Text(), nullable=False),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('access_token')
    )
    op.create_index(op.f('ix_wx_authorizer_app_id'), 'wx_authorizer', ['app_id'], unique=False)
    op.create_index(op.f('ix_wx_authorizer_master_uid'), 'wx_authorizer', ['master_uid'], unique=False)
    op.create_table('wx_authorizer_info',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('master_uid', sa.Integer(), nullable=True),
    sa.Column('app_id', sa.String(length=20), nullable=False),
    sa.Column('nick_name', sa.String(length=100), nullable=False),
    sa.Column('head_img', sa.String(length=100), nullable=True),
    sa.Column('user_name', sa.String(length=64), nullable=True),
    sa.Column('signature', sa.Text(), nullable=True),
    sa.Column('principal_name', sa.String(length=64), nullable=True),
    sa.Column('service_type_info', sa.String(length=100), nullable=True),
    sa.Column('verify_type_info', sa.String(length=100), nullable=True),
    sa.Column('business_info', sa.String(length=100), nullable=True),
    sa.Column('qrcode_url', sa.String(length=100), nullable=True),
    sa.Column('mini_program_info', sa.Text(), nullable=True),
    sa.Column('func_info', sa.Text(), nullable=False),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.Column('update_at', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wx_authorizer_info_app_id'), 'wx_authorizer_info', ['app_id'], unique=False)
    op.create_index(op.f('ix_wx_authorizer_info_master_uid'), 'wx_authorizer_info', ['master_uid'], unique=False)
    op.create_index(op.f('ix_wx_authorizer_info_nick_name'), 'wx_authorizer_info', ['nick_name'], unique=False)
    op.create_table('wx_tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('app_id', sa.String(length=20), nullable=True),
    sa.Column('info_type', sa.String(length=32), nullable=True),
    sa.Column('ticket', sa.String(length=128), nullable=False),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ticket')
    )
    op.create_index(op.f('ix_wx_tickets_app_id'), 'wx_tickets', ['app_id'], unique=False)
    op.create_table('wx_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('app_id', sa.String(length=20), nullable=True),
    sa.Column('access_token', sa.String(length=200), nullable=False),
    sa.Column('expires_in', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('access_token')
    )
    op.create_index(op.f('ix_wx_tokens_app_id'), 'wx_tokens', ['app_id'], unique=False)
    op.drop_index('ix_product_statistics_master_uid', table_name='product_statistics')
    op.create_index(op.f('ix_product_statistics_master_uid'), 'product_statistics', ['master_uid', 'sku_id', 'time', 'store_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_product_statistics_master_uid'), table_name='product_statistics')
    op.create_index('ix_product_statistics_master_uid', 'product_statistics', ['master_uid'], unique=False)
    op.drop_index(op.f('ix_wx_tokens_app_id'), table_name='wx_tokens')
    op.drop_table('wx_tokens')
    op.drop_index(op.f('ix_wx_tickets_app_id'), table_name='wx_tickets')
    op.drop_table('wx_tickets')
    op.drop_index(op.f('ix_wx_authorizer_info_nick_name'), table_name='wx_authorizer_info')
    op.drop_index(op.f('ix_wx_authorizer_info_master_uid'), table_name='wx_authorizer_info')
    op.drop_index(op.f('ix_wx_authorizer_info_app_id'), table_name='wx_authorizer_info')
    op.drop_table('wx_authorizer_info')
    op.drop_index(op.f('ix_wx_authorizer_master_uid'), table_name='wx_authorizer')
    op.drop_index(op.f('ix_wx_authorizer_app_id'), table_name='wx_authorizer')
    op.drop_table('wx_authorizer')
    op.drop_index(op.f('ix_wx_auth_codes_app_id'), table_name='wx_auth_codes')
    op.drop_table('wx_auth_codes')
    # ### end Alembic commands ###
