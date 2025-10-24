"""Add SmartPort models

Revision ID: 001
Revises:
Create Date: 2024-01-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    berth_type_enum = postgresql.ENUM('container', 'bulk', 'general_cargo', 'ro_ro', 'tanker', 'cruise', name='berthtype')
    berth_type_enum.create(op.get_bind())

    berth_status_enum = postgresql.ENUM('available', 'occupied', 'reserved', 'maintenance', 'unavailable', name='berthstatus')
    berth_status_enum.create(op.get_bind())

    vessel_type_enum = postgresql.ENUM('container_ship', 'bulk_carrier', 'tanker', 'general_cargo', 'ro_ro', 'cruise_ship', 'ferry', 'tugboat', 'other', name='vesseltype')
    vessel_type_enum.create(op.get_bind())

    vessel_status_enum = postgresql.ENUM('approaching', 'anchored', 'berthed', 'loading', 'unloading', 'departing', 'departed', name='vesselstatus')
    vessel_status_enum.create(op.get_bind())

    operation_type_enum = postgresql.ENUM('loading', 'unloading', 'bunkering', 'maintenance', 'inspection', 'passenger_operation', name='operationtype')
    operation_type_enum.create(op.get_bind())

    operation_status_enum = postgresql.ENUM('scheduled', 'in_progress', 'paused', 'completed', 'cancelled', 'delayed', name='operationstatus')
    operation_status_enum.create(op.get_bind())

    cargo_type_enum = postgresql.ENUM('containers', 'bulk_solid', 'bulk_liquid', 'general_cargo', 'vehicles', 'passengers', 'other', name='cargotype')
    cargo_type_enum.create(op.get_bind())

    # Create vessels table
    op.create_table(
        'vessels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, index=True),
        sa.Column('imo', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('mmsi', sa.String(20), nullable=True, unique=True),
        sa.Column('call_sign', sa.String(20), nullable=True),
        sa.Column('flag', sa.String(100), nullable=True),
        sa.Column('vessel_type', vessel_type_enum, nullable=False, index=True),
        sa.Column('status', vessel_status_enum, nullable=False, index=True),
        sa.Column('loa', sa.Float(), nullable=False),
        sa.Column('beam', sa.Float(), nullable=False),
        sa.Column('draft', sa.Float(), nullable=False),
        sa.Column('max_draft', sa.Float(), nullable=True),
        sa.Column('gross_tonnage', sa.Float(), nullable=True),
        sa.Column('deadweight_tonnage', sa.Float(), nullable=True),
        sa.Column('capacity_teu', sa.Integer(), nullable=True),
        sa.Column('capacity_passengers', sa.Integer(), nullable=True),
        sa.Column('capacity_vehicles', sa.Integer(), nullable=True),
        sa.Column('capacity_cubic_meters', sa.Float(), nullable=True),
        sa.Column('eta', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('ata', sa.DateTime(timezone=True), nullable=True),
        sa.Column('etd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('atd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_latitude', sa.Float(), nullable=True),
        sa.Column('last_longitude', sa.Float(), nullable=True),
        sa.Column('last_position_update', sa.DateTime(timezone=True), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('speed_knots', sa.Float(), nullable=True),
        sa.Column('origin_port', sa.String(200), nullable=True),
        sa.Column('destination_port', sa.String(200), nullable=True),
        sa.Column('voyage_number', sa.String(50), nullable=True),
        sa.Column('owner', sa.String(200), nullable=True),
        sa.Column('operator', sa.String(200), nullable=True),
        sa.Column('agent', sa.String(200), nullable=True),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create berths table
    op.create_table(
        'berths',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True),
        sa.Column('berth_type', berth_type_enum, nullable=False, index=True),
        sa.Column('status', berth_status_enum, nullable=False, index=True),
        sa.Column('max_loa', sa.Float(), nullable=False),
        sa.Column('max_beam', sa.Float(), nullable=False),
        sa.Column('max_draft', sa.Float(), nullable=False),
        sa.Column('max_displacement', sa.Float(), nullable=True),
        sa.Column('max_crane_capacity', sa.Float(), nullable=True),
        sa.Column('number_of_cranes', sa.Integer(), nullable=False, default=0),
        sa.Column('has_shore_power', sa.Boolean(), nullable=False, default=False),
        sa.Column('has_fresh_water', sa.Boolean(), nullable=False, default=False),
        sa.Column('has_bunker_facility', sa.Boolean(), nullable=False, default=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('current_vessel_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('occupation_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_departure', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['current_vessel_id'], ['vessels.id'], ),
    )

    # Create port_operations table
    op.create_table(
        'port_operations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vessel_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('berth_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('operation_type', operation_type_enum, nullable=False, index=True),
        sa.Column('status', operation_status_enum, nullable=False, index=True),
        sa.Column('cargo_type', cargo_type_enum, nullable=True),
        sa.Column('containers_planned', sa.Integer(), nullable=True),
        sa.Column('containers_completed', sa.Integer(), nullable=False, default=0),
        sa.Column('tonnage_planned', sa.Float(), nullable=True),
        sa.Column('tonnage_completed', sa.Float(), nullable=False, default=0.0),
        sa.Column('cubic_meters_planned', sa.Float(), nullable=True),
        sa.Column('cubic_meters_completed', sa.Float(), nullable=False, default=0.0),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cranes_assigned', sa.Integer(), nullable=False, default=0),
        sa.Column('workforce_assigned', sa.Integer(), nullable=False, default=0),
        sa.Column('equipment_used', postgresql.JSONB(), nullable=True),
        sa.Column('productivity_rate', sa.Float(), nullable=True),
        sa.Column('downtime_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('efficiency_percentage', sa.Float(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('actual_cost', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('priority', sa.Integer(), nullable=False, default=3),
        sa.Column('weather_delay', sa.Boolean(), nullable=False, default=False),
        sa.Column('equipment_delay', sa.Boolean(), nullable=False, default=False),
        sa.Column('labor_delay', sa.Boolean(), nullable=False, default=False),
        sa.Column('cargo_description', sa.String(500), nullable=True),
        sa.Column('special_requirements', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ),
    )

    # Create indexes
    op.create_index('ix_vessels_name', 'vessels', ['name'])
    op.create_index('ix_vessels_imo', 'vessels', ['imo'])
    op.create_index('ix_vessels_vessel_type', 'vessels', ['vessel_type'])
    op.create_index('ix_vessels_status', 'vessels', ['status'])
    op.create_index('ix_vessels_eta', 'vessels', ['eta'])

    op.create_index('ix_berths_name', 'berths', ['name'])
    op.create_index('ix_berths_berth_type', 'berths', ['berth_type'])
    op.create_index('ix_berths_status', 'berths', ['status'])

    op.create_index('ix_port_operations_vessel_id', 'port_operations', ['vessel_id'])
    op.create_index('ix_port_operations_berth_id', 'port_operations', ['berth_id'])
    op.create_index('ix_port_operations_operation_type', 'port_operations', ['operation_type'])
    op.create_index('ix_port_operations_status', 'port_operations', ['status'])
    op.create_index('ix_port_operations_scheduled_start', 'port_operations', ['scheduled_start'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('port_operations')
    op.drop_table('berths')
    op.drop_table('vessels')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS cargotype')
    op.execute('DROP TYPE IF EXISTS operationstatus')
    op.execute('DROP TYPE IF EXISTS operationtype')
    op.execute('DROP TYPE IF EXISTS vesselstatus')
    op.execute('DROP TYPE IF EXISTS vesseltype')
    op.execute('DROP TYPE IF EXISTS berthstatus')
    op.execute('DROP TYPE IF EXISTS berthtype')
