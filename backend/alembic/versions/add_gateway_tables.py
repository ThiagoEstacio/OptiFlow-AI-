"""add gateway tables

Revision ID: add_gateway_tables
Revises: add_asset_health_history
Create Date: 2025-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_gateway_tables'
down_revision = 'add_asset_health_history'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create gateway_type enum
    gateway_type_enum = postgresql.ENUM(
        'opcua', 'modbus_tcp', 'siemens_s7', 'rockwell_eip',
        name='gatewaytype',
        create_type=False
    )
    gateway_type_enum.create(op.get_bind(), checkfirst=True)

    # Create gateway_configs table
    op.create_table(
        'gateway_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('gateway_type', gateway_type_enum, nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('connection_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('polling_interval_ms', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('base_retry_delay', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_buffer_size', sa.Integer(), nullable=False, server_default='10000'),
        sa.Column('description', sa.String(length=500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_gateway_configs_id', 'gateway_configs', ['id'])
    op.create_index('ix_gateway_configs_name', 'gateway_configs', ['name'], unique=True)
    op.create_index('ix_gateway_configs_gateway_type', 'gateway_configs', ['gateway_type'])

    # Create gateway_tags table
    op.create_table(
        'gateway_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gateway_id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(length=200), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('address_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('data_type', sa.String(length=50), server_default='float'),
        sa.Column('scale_factor', sa.Float(), server_default='1.0'),
        sa.Column('offset', sa.Float(), server_default='0.0'),
        sa.Column('unit', sa.String(length=50)),
        sa.Column('description', sa.String(length=500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['gateway_id'], ['gateway_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for gateway_tags
    op.create_index('ix_gateway_tags_id', 'gateway_tags', ['id'])
    op.create_index('ix_gateway_tags_tag_name', 'gateway_tags', ['tag_name'])
    op.create_index('ix_gateway_tags_gateway_id', 'gateway_tags', ['gateway_id'])

    # Create gateway_health_logs table
    op.create_table(
        'gateway_health_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gateway_name', sa.String(length=200), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('successful_reads', sa.Integer(), server_default='0'),
        sa.Column('failed_reads', sa.Integer(), server_default='0'),
        sa.Column('buffer_size', sa.Integer(), server_default='0'),
        sa.Column('uptime_seconds', sa.Float()),
        sa.Column('last_error', sa.String(length=1000)),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for health logs
    op.create_index('ix_gateway_health_logs_id', 'gateway_health_logs', ['id'])
    op.create_index('ix_gateway_health_logs_gateway_name', 'gateway_health_logs', ['gateway_name'])
    op.create_index('ix_gateway_health_logs_timestamp', 'gateway_health_logs', ['timestamp'])

    # Composite index for time-series queries
    op.create_index('ix_gateway_health_logs_name_time', 'gateway_health_logs', ['gateway_name', 'timestamp'])


def downgrade() -> None:
    # Drop tables
    op.drop_index('ix_gateway_health_logs_name_time', table_name='gateway_health_logs')
    op.drop_index('ix_gateway_health_logs_timestamp', table_name='gateway_health_logs')
    op.drop_index('ix_gateway_health_logs_gateway_name', table_name='gateway_health_logs')
    op.drop_index('ix_gateway_health_logs_id', table_name='gateway_health_logs')
    op.drop_table('gateway_health_logs')

    op.drop_index('ix_gateway_tags_gateway_id', table_name='gateway_tags')
    op.drop_index('ix_gateway_tags_tag_name', table_name='gateway_tags')
    op.drop_index('ix_gateway_tags_id', table_name='gateway_tags')
    op.drop_table('gateway_tags')

    op.drop_index('ix_gateway_configs_gateway_type', table_name='gateway_configs')
    op.drop_index('ix_gateway_configs_name', table_name='gateway_configs')
    op.drop_index('ix_gateway_configs_id', table_name='gateway_configs')
    op.drop_table('gateway_configs')

    # Drop enum
    gateway_type_enum = postgresql.ENUM(
        'opcua', 'modbus_tcp', 'siemens_s7', 'rockwell_eip',
        name='gatewaytype'
    )
    gateway_type_enum.drop(op.get_bind(), checkfirst=True)
