"""add asset health alerts

Revision ID: add_asset_health_alerts
Revises: add_asset_framework
Create Date: 2025-11-03 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_asset_health_alerts'
down_revision = 'add_asset_framework'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE healthalertseverity AS ENUM ('critical', 'high', 'medium', 'low');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE healthalertstate AS ENUM ('active', 'acknowledged', 'resolved');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create asset_health_alerts table
    op.create_table(
        'asset_health_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),

        # Alert information
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', name='healthalertseverity'), nullable=False),
        sa.Column('state', sa.Enum('active', 'acknowledged', 'resolved', name='healthalertstate'), nullable=False, server_default='active'),

        # Health metrics
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('health_status', sa.String(50), nullable=False),
        sa.Column('issues_count', sa.Float(), nullable=False, server_default='0'),
        sa.Column('warnings_count', sa.Float(), nullable=False, server_default='0'),

        # JSON columns
        sa.Column('problematic_attributes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('recommendations', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('alert_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),

        # Acknowledgment
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('acknowledgment_comment', sa.Text(), nullable=True),

        # Resolution
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolution_comment', sa.Text(), nullable=True),
        sa.Column('resolved_health_score', sa.Float(), nullable=True),

        # Notification
        sa.Column('notification_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),

        # Auto-resolution
        sa.Column('auto_resolved', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for better query performance
    op.create_index('ix_asset_health_alerts_asset_id', 'asset_health_alerts', ['asset_id'])
    op.create_index('ix_asset_health_alerts_severity', 'asset_health_alerts', ['severity'])
    op.create_index('ix_asset_health_alerts_state', 'asset_health_alerts', ['state'])
    op.create_index('ix_asset_health_alerts_triggered_at', 'asset_health_alerts', ['triggered_at'])

    # Create composite index for common query patterns
    op.create_index('ix_asset_health_alerts_state_severity', 'asset_health_alerts', ['state', 'severity'])


def downgrade():
    # Drop table and indexes
    op.drop_index('ix_asset_health_alerts_state_severity', table_name='asset_health_alerts')
    op.drop_index('ix_asset_health_alerts_triggered_at', table_name='asset_health_alerts')
    op.drop_index('ix_asset_health_alerts_state', table_name='asset_health_alerts')
    op.drop_index('ix_asset_health_alerts_severity', table_name='asset_health_alerts')
    op.drop_index('ix_asset_health_alerts_asset_id', table_name='asset_health_alerts')
    op.drop_table('asset_health_alerts')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS healthalertstate')
    op.execute('DROP TYPE IF EXISTS healthalertseverity')
