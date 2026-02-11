"""V2 phase1: expand User, add TrustedIP PinAttempt AppConfig

Revision ID: c19e0605deb4
Revises: 14a4d39f7b23
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c19e0605deb4'
down_revision = '14a4d39f7b23'
branch_labels = None
depends_on = None


def upgrade():
    # New tables
    op.create_table('app_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_table('trusted_ip',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('trusted_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ip_address')
    )
    op.create_table('pin_attempt',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Expand User table with V2 columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('allowance', sa.Float(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('icon', sa.String(length=50), server_default="'question_mark'", nullable=True))
        batch_op.add_column(sa.Column('theme_color', sa.String(length=20), server_default="'cyan'", nullable=True))
        batch_op.add_column(sa.Column('xp', sa.Integer(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('level', sa.Integer(), server_default='1', nullable=True))
        batch_op.add_column(sa.Column('streak_current', sa.Integer(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('streak_best', sa.Integer(), server_default='0', nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('streak_best')
        batch_op.drop_column('streak_current')
        batch_op.drop_column('level')
        batch_op.drop_column('xp')
        batch_op.drop_column('theme_color')
        batch_op.drop_column('icon')
        batch_op.drop_column('is_admin')
        batch_op.drop_column('allowance')
        batch_op.drop_column('email')

    op.drop_table('pin_attempt')
    op.drop_table('trusted_ip')
    op.drop_table('app_config')
