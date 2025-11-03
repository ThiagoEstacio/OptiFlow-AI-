"""add asset health history

Revision ID: add_asset_health_history
Revises: add_asset_health_alerts
Create Date: 2025-11-03 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_asset_health_history'
down_revision = 'add_asset_health_alerts'
branch_labels = None
depends_on = None


def upgrade():
    # Create asset_health_history table
    op.create_table(
        'asset_health_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),

        # Snapshot timestamp
        sa.Column('snapshot_time', sa.DateTime(timezone=True), nullable=False),

        # Health metrics
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('health_status', sa.String(50), nullable=False),

        # Issue counts
        sa.Column('issues_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('warnings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attributes_evaluated', sa.Integer(), nullable=False, server_default='0'),

        # JSON columns
        sa.Column('attribute_scores', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('issues_snapshot', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('warnings_snapshot', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('asset_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),

        # Statistical metrics
        sa.Column('health_score_change', sa.Float(), nullable=True),
        sa.Column('trend_direction', sa.String(20), nullable=True),
        sa.Column('velocity', sa.Float(), nullable=True),

        # Record metadata
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for efficient querying
    op.create_index('ix_asset_health_history_asset_id', 'asset_health_history', ['asset_id'])
    op.create_index('ix_asset_health_history_snapshot_time', 'asset_health_history', ['snapshot_time'])
    op.create_index('ix_asset_health_history_health_score', 'asset_health_history', ['health_score'])
    op.create_index('ix_asset_health_history_health_status', 'asset_health_history', ['health_status'])

    # Composite indexes for common query patterns
    op.create_index(
        'ix_asset_health_history_asset_time',
        'asset_health_history',
        ['asset_id', 'snapshot_time'],
        unique=False
    )

    op.create_index(
        'ix_asset_health_history_time_score',
        'asset_health_history',
        ['snapshot_time', 'health_score'],
        unique=False
    )

    # Create index for trend analysis
    op.create_index(
        'ix_asset_health_history_trend',
        'asset_health_history',
        ['asset_id', 'trend_direction', 'snapshot_time'],
        unique=False
    )


def downgrade():
    # Drop indexes
    op.drop_index('ix_asset_health_history_trend', table_name='asset_health_history')
    op.drop_index('ix_asset_health_history_time_score', table_name='asset_health_history')
    op.drop_index('ix_asset_health_history_asset_time', table_name='asset_health_history')
    op.drop_index('ix_asset_health_history_health_status', table_name='asset_health_history')
    op.drop_index('ix_asset_health_history_health_score', table_name='asset_health_history')
    op.drop_index('ix_asset_health_history_snapshot_time', table_name='asset_health_history')
    op.drop_index('ix_asset_health_history_asset_id', table_name='asset_health_history')

    # Drop table
    op.drop_table('asset_health_history')
