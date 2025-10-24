"""Create SmartPort tables for port operations management

Revision ID: 001_smartport
Revises:
Create Date: 2025-01-24 00:00:00.000000

This migration creates all tables needed for the SmartPort MVP:
- vessels: Ship/vessel management
- berths: Port berth/terminal infrastructure
- loading_operations: Cargo loading/unloading operations
- cargos: Commodity details
- operation_events: Operation timeline tracking
- port_equipment: Port handling equipment
- maintenance_records: Equipment maintenance history
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_smartport'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create SmartPort tables"""

    # ===== 1. CREATE VESSELS TABLE =====
    op.create_table(
        'vessels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Vessel identification
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('imo_number', sa.String(20), nullable=False, unique=True),
        sa.Column('call_sign', sa.String(20), nullable=True),
        sa.Column('mmsi', sa.String(20), nullable=True),

        # Vessel information
        sa.Column('vessel_type', sa.String(50), nullable=False),
        sa.Column('flag', sa.String(100), nullable=True),
        sa.Column('classification', sa.String(100), nullable=True),

        # Vessel specifications
        sa.Column('dwt', sa.Float, nullable=True),
        sa.Column('grt', sa.Float, nullable=True),
        sa.Column('nrt', sa.Float, nullable=True),
        sa.Column('length', sa.Float, nullable=True),
        sa.Column('beam', sa.Float, nullable=True),
        sa.Column('draft', sa.Float, nullable=True),
        sa.Column('capacity', sa.Float, nullable=True),

        # Ownership
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('operator', sa.String(255), nullable=True),
        sa.Column('agent', sa.String(255), nullable=True),

        # Status
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('current_berth_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Schedule
        sa.Column('eta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ata', sa.DateTime(timezone=True), nullable=True),
        sa.Column('etb', sa.DateTime(timezone=True), nullable=True),
        sa.Column('atb', sa.DateTime(timezone=True), nullable=True),
        sa.Column('etc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('atc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('etd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('atd', sa.DateTime(timezone=True), nullable=True),

        # Additional info
        sa.Column('voyage_number', sa.String(50), nullable=True),
        sa.Column('previous_port', sa.String(100), nullable=True),
        sa.Column('next_port', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),

        # Metadata
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
    )

    # Create indexes for vessels
    op.create_index('ix_vessels_site_id', 'vessels', ['site_id'])
    op.create_index('ix_vessels_name', 'vessels', ['name'])
    op.create_index('ix_vessels_imo_number', 'vessels', ['imo_number'])
    op.create_index('ix_vessels_status', 'vessels', ['status'])
    op.create_index('ix_vessels_current_berth_id', 'vessels', ['current_berth_id'])

    # ===== 2. CREATE BERTHS TABLE =====
    op.create_table(
        'berths',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Berth identification
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('berth_type', sa.String(50), nullable=False),

        # Physical specifications
        sa.Column('length', sa.Float, nullable=True),
        sa.Column('depth', sa.Float, nullable=True),
        sa.Column('max_draft', sa.Float, nullable=True),
        sa.Column('max_dwt', sa.Float, nullable=True),
        sa.Column('max_loa', sa.Float, nullable=True),

        # Capacity & equipment
        sa.Column('loading_rate', sa.Float, nullable=True),
        sa.Column('unloading_rate', sa.Float, nullable=True),
        sa.Column('storage_capacity', sa.Float, nullable=True),
        sa.Column('num_shiploaders', sa.Integer, nullable=False, server_default='0'),
        sa.Column('num_conveyors', sa.Integer, nullable=False, server_default='0'),
        sa.Column('num_cranes', sa.Integer, nullable=False, server_default='0'),

        # Location
        sa.Column('latitude', sa.String(50), nullable=True),
        sa.Column('longitude', sa.String(50), nullable=True),

        # Status
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('current_vessel_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('available_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('available_until', sa.DateTime(timezone=True), nullable=True),

        # Commodities
        sa.Column('commodities', postgresql.JSONB, nullable=False, server_default='[]'),

        # Additional info
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('restrictions', sa.Text, nullable=True),

        # Metadata
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
    )

    # Create indexes for berths
    op.create_index('ix_berths_site_id', 'berths', ['site_id'])
    op.create_index('ix_berths_code', 'berths', ['code'])
    op.create_index('ix_berths_status', 'berths', ['status'])
    op.create_index('ix_berths_berth_type', 'berths', ['berth_type'])

    # Add foreign key from vessels to berths (now that berths table exists)
    op.create_foreign_key(
        'fk_vessels_current_berth_id',
        'vessels', 'berths',
        ['current_berth_id'], ['id'],
        ondelete='SET NULL'
    )

    # ===== 3. CREATE LOADING_OPERATIONS TABLE =====
    op.create_table(
        'loading_operations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vessel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('berth_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Operation details
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('operation_number', sa.String(100), nullable=False, unique=True),
        sa.Column('status', sa.String(50), nullable=False),

        # Schedule
        sa.Column('planned_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('planned_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),

        # Performance metrics
        sa.Column('planned_rate', sa.Float, nullable=True),
        sa.Column('actual_rate', sa.Float, nullable=True),
        sa.Column('current_rate', sa.Float, nullable=True),
        sa.Column('total_planned_quantity', sa.Float, nullable=False),
        sa.Column('total_actual_quantity', sa.Float, nullable=False, server_default='0'),
        sa.Column('efficiency', sa.Float, nullable=True),
        sa.Column('downtime_hours', sa.Float, nullable=False, server_default='0'),
        sa.Column('working_hours', sa.Float, nullable=False, server_default='0'),

        # Delay tracking
        sa.Column('is_delayed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('delay_reason', sa.Text, nullable=True),
        sa.Column('delay_minutes', sa.Float, nullable=False, server_default='0'),

        # Equipment
        sa.Column('equipment_used', postgresql.JSONB, nullable=False, server_default='[]'),

        # Additional info
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('weather_conditions', sa.String(255), nullable=True),
        sa.Column('shift_supervisor', sa.String(255), nullable=True),

        # Metadata
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ondelete='CASCADE'),
    )

    # Create indexes for loading_operations
    op.create_index('ix_loading_operations_site_id', 'loading_operations', ['site_id'])
    op.create_index('ix_loading_operations_vessel_id', 'loading_operations', ['vessel_id'])
    op.create_index('ix_loading_operations_berth_id', 'loading_operations', ['berth_id'])
    op.create_index('ix_loading_operations_operation_number', 'loading_operations', ['operation_number'])
    op.create_index('ix_loading_operations_status', 'loading_operations', ['status'])
    op.create_index('ix_loading_operations_operation_type', 'loading_operations', ['operation_type'])

    # ===== 4. CREATE CARGOS TABLE =====
    op.create_table(
        'cargos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loading_operation_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Cargo details
        sa.Column('commodity', sa.String(50), nullable=False),
        sa.Column('commodity_grade', sa.String(100), nullable=True),
        sa.Column('description', sa.Text, nullable=True),

        # Quantity
        sa.Column('planned_quantity', sa.Float, nullable=False),
        sa.Column('actual_quantity', sa.Float, nullable=True),
        sa.Column('unit', sa.String(20), nullable=False, server_default='tons'),

        # Origin & destination
        sa.Column('origin', sa.String(255), nullable=True),
        sa.Column('destination', sa.String(255), nullable=True),
        sa.Column('shipper', sa.String(255), nullable=True),
        sa.Column('consignee', sa.String(255), nullable=True),

        # Quality & specifications
        sa.Column('specifications', postgresql.JSONB, nullable=False, server_default='{}'),

        # Additional info
        sa.Column('bl_number', sa.String(100), nullable=True),
        sa.Column('customs_reference', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),

        # Metadata
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['loading_operation_id'], ['loading_operations.id'], ondelete='CASCADE'),
    )

    # Create indexes for cargos
    op.create_index('ix_cargos_loading_operation_id', 'cargos', ['loading_operation_id'])
    op.create_index('ix_cargos_commodity', 'cargos', ['commodity'])

    # ===== 5. CREATE OPERATION_EVENTS TABLE =====
    op.create_table(
        'operation_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loading_operation_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Event details
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('event_data', postgresql.JSONB, nullable=False, server_default='{}'),

        # User info
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_name', sa.String(255), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['loading_operation_id'], ['loading_operations.id'], ondelete='CASCADE'),
    )

    # Create indexes for operation_events
    op.create_index('ix_operation_events_loading_operation_id', 'operation_events', ['loading_operation_id'])
    op.create_index('ix_operation_events_event_type', 'operation_events', ['event_type'])
    op.create_index('ix_operation_events_event_time', 'operation_events', ['event_time'])

    # ===== 6. CREATE PORT_EQUIPMENT TABLE =====
    op.create_table(
        'port_equipment',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('berth_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Equipment identification
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('equipment_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Equipment specifications
        sa.Column('manufacturer', sa.String(255), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('year_manufactured', sa.Integer, nullable=True),
        sa.Column('year_installed', sa.Integer, nullable=True),

        # Performance specifications
        sa.Column('rated_capacity', sa.Float, nullable=True),
        sa.Column('max_capacity', sa.Float, nullable=True),
        sa.Column('design_speed', sa.Float, nullable=True),
        sa.Column('power_rating', sa.Float, nullable=True),

        # Current status
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('health_score', sa.Float, nullable=True),
        sa.Column('failure_probability', sa.Float, nullable=True),
        sa.Column('remaining_useful_life', sa.Integer, nullable=True),

        # Operational metrics
        sa.Column('total_operating_hours', sa.Float, nullable=False, server_default='0'),
        sa.Column('total_downtime_hours', sa.Float, nullable=False, server_default='0'),
        sa.Column('total_throughput', sa.Float, nullable=False, server_default='0'),
        sa.Column('current_throughput', sa.Float, nullable=True),

        # Maintenance tracking
        sa.Column('last_maintenance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_maintenance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('maintenance_interval_hours', sa.Float, nullable=True),

        # Alarm thresholds
        sa.Column('alarm_thresholds', postgresql.JSONB, nullable=False, server_default='{}'),

        # Location
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('latitude', sa.String(50), nullable=True),
        sa.Column('longitude', sa.String(50), nullable=True),

        # Additional info
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('criticality', sa.String(20), nullable=True),

        # Metadata
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
    )

    # Create indexes for port_equipment
    op.create_index('ix_port_equipment_site_id', 'port_equipment', ['site_id'])
    op.create_index('ix_port_equipment_berth_id', 'port_equipment', ['berth_id'])
    op.create_index('ix_port_equipment_device_id', 'port_equipment', ['device_id'])
    op.create_index('ix_port_equipment_code', 'port_equipment', ['code'])
    op.create_index('ix_port_equipment_equipment_type', 'port_equipment', ['equipment_type'])
    op.create_index('ix_port_equipment_status', 'port_equipment', ['status'])

    # ===== 7. CREATE MAINTENANCE_RECORDS TABLE =====
    op.create_table(
        'maintenance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Maintenance details
        sa.Column('maintenance_type', sa.String(50), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_hours', sa.Float, nullable=True),

        # Work performed
        sa.Column('work_description', sa.Text, nullable=False),
        sa.Column('parts_replaced', postgresql.JSONB, nullable=False, server_default='[]'),

        # Costs
        sa.Column('labor_cost', sa.Float, nullable=True),
        sa.Column('parts_cost', sa.Float, nullable=True),
        sa.Column('total_cost', sa.Float, nullable=True),

        # Personnel
        sa.Column('technician_name', sa.String(255), nullable=True),
        sa.Column('supervisor_name', sa.String(255), nullable=True),

        # Findings & recommendations
        sa.Column('findings', sa.Text, nullable=True),
        sa.Column('recommendations', sa.Text, nullable=True),
        sa.Column('next_maintenance_date', sa.DateTime(timezone=True), nullable=True),

        # Additional info
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('attachments', postgresql.JSONB, nullable=False, server_default='[]'),

        # Metadata
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['equipment_id'], ['port_equipment.id'], ondelete='CASCADE'),
    )

    # Create indexes for maintenance_records
    op.create_index('ix_maintenance_records_equipment_id', 'maintenance_records', ['equipment_id'])
    op.create_index('ix_maintenance_records_maintenance_type', 'maintenance_records', ['maintenance_type'])
    op.create_index('ix_maintenance_records_actual_date', 'maintenance_records', ['actual_date'])


def downgrade() -> None:
    """Drop SmartPort tables in reverse order"""

    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_table('maintenance_records')
    op.drop_table('port_equipment')
    op.drop_table('operation_events')
    op.drop_table('cargos')
    op.drop_table('loading_operations')

    # Drop foreign key from vessels before dropping berths
    op.drop_constraint('fk_vessels_current_berth_id', 'vessels', type_='foreignkey')

    op.drop_table('berths')
    op.drop_table('vessels')
