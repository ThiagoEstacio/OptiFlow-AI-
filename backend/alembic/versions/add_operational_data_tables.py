"""add operational data tables

Revision ID: add_operational_data_tables
Revises: add_gateway_tables
Create Date: 2025-11-03 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_operational_data_tables'
down_revision = 'add_gateway_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create truck_entries table
    op.create_table(
        'truck_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('truck_id', sa.String(length=50), nullable=False),
        sa.Column('driver_name', sa.String(length=200)),
        sa.Column('company', sa.String(length=200)),
        sa.Column('gross_weight', sa.Float(), nullable=False),
        sa.Column('tare_weight', sa.Float(), nullable=False),
        sa.Column('net_weight', sa.Float(), nullable=False),
        sa.Column('product_type', sa.String(length=100), nullable=False),
        sa.Column('product_quality', sa.String(length=50)),
        sa.Column('moisture_percent', sa.Float()),
        sa.Column('impurity_percent', sa.Float()),
        sa.Column('origin_farm', sa.String(length=200)),
        sa.Column('origin_city', sa.String(length=200)),
        sa.Column('origin_state', sa.String(length=50)),
        sa.Column('entry_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('gross_weight_time', sa.DateTime(timezone=True)),
        sa.Column('tare_weight_time', sa.DateTime(timezone=True)),
        sa.Column('exit_time', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(length=50), server_default='pending'),
        sa.Column('notes', sa.Text()),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for truck_entries
    op.create_index('ix_truck_entries_id', 'truck_entries', ['id'])
    op.create_index('ix_truck_entries_truck_id', 'truck_entries', ['truck_id'])
    op.create_index('ix_truck_entries_product_type', 'truck_entries', ['product_type'])
    op.create_index('ix_truck_entries_entry_time', 'truck_entries', ['entry_time'])
    op.create_index('ix_truck_entries_status', 'truck_entries', ['status'])
    op.create_index('ix_truck_entries_site_date', 'truck_entries', ['site_id', 'entry_time'])

    # Create ship_loadings table
    op.create_table(
        'ship_loadings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ship_name', sa.String(length=200), nullable=False),
        sa.Column('ship_imo', sa.String(length=20)),
        sa.Column('ship_flag', sa.String(length=50)),
        sa.Column('ship_dwt', sa.Float()),
        sa.Column('berth_number', sa.Integer(), nullable=False),
        sa.Column('product_type', sa.String(length=100), nullable=False),
        sa.Column('target_tonnage', sa.Float(), nullable=False),
        sa.Column('loaded_tonnage', sa.Float(), server_default='0.0'),
        sa.Column('loading_rate_avg', sa.Float()),
        sa.Column('loading_rate_peak', sa.Float()),
        sa.Column('downtime_hours', sa.Float(), server_default='0.0'),
        sa.Column('arrival_time', sa.DateTime(timezone=True)),
        sa.Column('berthing_time', sa.DateTime(timezone=True)),
        sa.Column('loading_start_time', sa.DateTime(timezone=True)),
        sa.Column('loading_end_time', sa.DateTime(timezone=True)),
        sa.Column('departure_time', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(length=50), server_default='scheduled'),
        sa.Column('buyer_company', sa.String(length=200)),
        sa.Column('destination_port', sa.String(length=200)),
        sa.Column('destination_country', sa.String(length=100)),
        sa.Column('contract_number', sa.String(length=100)),
        sa.Column('average_moisture', sa.Float()),
        sa.Column('average_impurity', sa.Float()),
        sa.Column('quality_approved', sa.Boolean(), server_default='true'),
        sa.Column('quality_notes', sa.Text()),
        sa.Column('weather_conditions', sa.String(length=200)),
        sa.Column('incidents', sa.Text()),
        sa.Column('notes', sa.Text()),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for ship_loadings
    op.create_index('ix_ship_loadings_id', 'ship_loadings', ['id'])
    op.create_index('ix_ship_loadings_ship_name', 'ship_loadings', ['ship_name'])
    op.create_index('ix_ship_loadings_berth_number', 'ship_loadings', ['berth_number'])
    op.create_index('ix_ship_loadings_product_type', 'ship_loadings', ['product_type'])
    op.create_index('ix_ship_loadings_arrival_time', 'ship_loadings', ['arrival_time'])
    op.create_index('ix_ship_loadings_status', 'ship_loadings', ['status'])
    op.create_index('ix_ship_loadings_site_date', 'ship_loadings', ['site_id', 'arrival_time'])

    # Create daily_operations table
    op.create_table(
        'daily_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation_date', sa.Date(), nullable=False),
        sa.Column('trucks_received', sa.Integer(), server_default='0'),
        sa.Column('trucks_total_tonnage', sa.Float(), server_default='0.0'),
        sa.Column('trucks_avg_wait_time', sa.Float()),
        sa.Column('ships_in_port', sa.Integer(), server_default='0'),
        sa.Column('ships_loading', sa.Integer(), server_default='0'),
        sa.Column('ships_departed', sa.Integer(), server_default='0'),
        sa.Column('ships_total_tonnage', sa.Float(), server_default='0.0'),
        sa.Column('total_tonnage_loaded', sa.Float(), server_default='0.0'),
        sa.Column('avg_loading_rate', sa.Float()),
        sa.Column('operating_hours', sa.Float(), server_default='0.0'),
        sa.Column('downtime_hours', sa.Float(), server_default='0.0'),
        sa.Column('shiploaders_available', sa.Integer()),
        sa.Column('shiploaders_operating', sa.Integer()),
        sa.Column('conveyors_available', sa.Integer()),
        sa.Column('conveyors_operating', sa.Integer()),
        sa.Column('corn_tonnage', sa.Float(), server_default='0.0'),
        sa.Column('soy_tonnage', sa.Float(), server_default='0.0'),
        sa.Column('wheat_tonnage', sa.Float(), server_default='0.0'),
        sa.Column('other_tonnage', sa.Float(), server_default='0.0'),
        sa.Column('weather_condition', sa.String(length=100)),
        sa.Column('avg_temperature', sa.Float()),
        sa.Column('rainfall_mm', sa.Float()),
        sa.Column('wind_speed_kmh', sa.Float()),
        sa.Column('weather_delays_hours', sa.Float(), server_default='0.0'),
        sa.Column('incidents_count', sa.Integer(), server_default='0'),
        sa.Column('incidents_description', sa.Text()),
        sa.Column('maintenance_hours', sa.Float(), server_default='0.0'),
        sa.Column('operational_efficiency', sa.Float()),
        sa.Column('equipment_utilization', sa.Float()),
        sa.Column('notes', sa.Text()),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for daily_operations
    op.create_index('ix_daily_operations_id', 'daily_operations', ['id'])
    op.create_index('ix_daily_operations_operation_date', 'daily_operations', ['operation_date'])
    op.create_index('ix_daily_operations_site_date', 'daily_operations', ['site_id', 'operation_date'], unique=True)


def downgrade() -> None:
    # Drop daily_operations table
    op.drop_index('ix_daily_operations_site_date', table_name='daily_operations')
    op.drop_index('ix_daily_operations_operation_date', table_name='daily_operations')
    op.drop_index('ix_daily_operations_id', table_name='daily_operations')
    op.drop_table('daily_operations')

    # Drop ship_loadings table
    op.drop_index('ix_ship_loadings_site_date', table_name='ship_loadings')
    op.drop_index('ix_ship_loadings_status', table_name='ship_loadings')
    op.drop_index('ix_ship_loadings_arrival_time', table_name='ship_loadings')
    op.drop_index('ix_ship_loadings_product_type', table_name='ship_loadings')
    op.drop_index('ix_ship_loadings_berth_number', table_name='ship_loadings')
    op.drop_index('ix_ship_loadings_ship_name', table_name='ship_loadings')
    op.drop_index('ix_ship_loadings_id', table_name='ship_loadings')
    op.drop_table('ship_loadings')

    # Drop truck_entries table
    op.drop_index('ix_truck_entries_site_date', table_name='truck_entries')
    op.drop_index('ix_truck_entries_status', table_name='truck_entries')
    op.drop_index('ix_truck_entries_entry_time', table_name='truck_entries')
    op.drop_index('ix_truck_entries_product_type', table_name='truck_entries')
    op.drop_index('ix_truck_entries_truck_id', table_name='truck_entries')
    op.drop_index('ix_truck_entries_id', table_name='truck_entries')
    op.drop_table('truck_entries')
