"""add wx_service_message table

Revision ID: dd01791162ea
Revises: ff8d961af1ba
Create Date: 2018-03-11 17:00:17.798226

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd01791162ea'
down_revision = 'ff8d961af1ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wx_service_from',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('master_uid', sa.Integer(), nullable=True),
    sa.Column('auth_app_id', sa.String(length=32), nullable=False),
    sa.Column('session_from', sa.String(length=100), nullable=True),
    sa.Column('from_user', sa.String(length=100), nullable=True),
    sa.Column('create_time', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wx_service_from_auth_app_id'), 'wx_service_from', ['auth_app_id'], unique=False)
    op.create_index(op.f('ix_wx_service_from_master_uid'), 'wx_service_from', ['master_uid'], unique=False)
    op.create_table('wx_service_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('master_uid', sa.Integer(), nullable=True),
    sa.Column('auth_app_id', sa.String(length=32), nullable=False),
    sa.Column('to_user', sa.String(length=100), nullable=True),
    sa.Column('from_user', sa.String(length=100), nullable=True),
    sa.Column('msg_type', sa.String(length=32), nullable=True),
    sa.Column('msg_id', sa.String(length=100), nullable=True),
    sa.Column('create_time', sa.Integer(), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('pic_url', sa.String(length=100), nullable=True),
    sa.Column('media_id', sa.String(length=32), nullable=True),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('url', sa.String(length=200), nullable=True),
    sa.Column('title', sa.String(length=100), nullable=True),
    sa.Column('app_id', sa.String(length=64), nullable=True),
    sa.Column('page_path', sa.String(length=200), nullable=True),
    sa.Column('thumb_url', sa.String(length=200), nullable=True),
    sa.Column('thumb_media_id', sa.String(length=64), nullable=True),
    sa.Column('type', sa.SmallInteger(), nullable=True),
    sa.Column('send_at', sa.Integer(), nullable=True),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('reason', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wx_service_messages_auth_app_id'), 'wx_service_messages', ['auth_app_id'], unique=False)
    op.create_index(op.f('ix_wx_service_messages_master_uid'), 'wx_service_messages', ['master_uid'], unique=False)
    op.add_column('wx_mini_apps', sa.Column('service_aes_key', sa.String(length=64), nullable=True))
    op.add_column('wx_mini_apps', sa.Column('service_token', sa.String(length=100), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('wx_mini_apps', 'service_token')
    op.drop_column('wx_mini_apps', 'service_aes_key')
    op.drop_index(op.f('ix_wx_service_messages_master_uid'), table_name='wx_service_messages')
    op.drop_index(op.f('ix_wx_service_messages_auth_app_id'), table_name='wx_service_messages')
    op.drop_table('wx_service_messages')
    op.drop_index(op.f('ix_wx_service_from_master_uid'), table_name='wx_service_from')
    op.drop_index(op.f('ix_wx_service_from_auth_app_id'), table_name='wx_service_from')
    op.drop_table('wx_service_from')
    # ### end Alembic commands ###
