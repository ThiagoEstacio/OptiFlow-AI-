"""add_asset_framework_tables

Revision ID: add_asset_framework
Revises: add_tag_labels
Create Date: 2025-11-03 15:00:00.000000

Creates asset framework tables for hierarchical organization similar to PI Vision Asset Framework:
- assets: Hierarchical asset structure (Enterprise → Site → Area → Equipment)
- asset_attributes: Links assets to tags or contains static/calculated values
- asset_templates: Reusable asset definitions for instantiation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_asset_framework'
down_revision = 'add_tag_labels'
branch_labels = None
depends_on = None


def upgrade():
    # Create asset_templates table first (no dependencies)
    op.create_table(
        'asset_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Template info
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', sa.Enum(
            'enterprise', 'site', 'area', 'unit', 'equipment', 'component',
            name='assettype',
            create_type=True
        ), nullable=False),

        # Template definition (JSON)
        sa.Column('attribute_definitions', postgresql.JSONB(asdict=False), nullable=False, server_default='[]'),
        sa.Column('analyses', postgresql.JSONB(asdict=False), nullable=False, server_default='[]'),

        # Active flag
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create indexes for asset_templates
    op.create_index('ix_asset_templates_name', 'asset_templates', ['name'])
    op.create_index('ix_asset_templates_asset_type', 'asset_templates', ['asset_type'])

    # Create assets table
    op.create_table(
        'assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Basic info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', sa.Enum(
            'enterprise', 'site', 'area', 'unit', 'equipment', 'component',
            name='assettype',
            create_type=False  # Already created above
        ), nullable=False),

        # Hierarchy - self-referential foreign key
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Optional template reference
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Active flag
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Additional metadata (flexible JSON storage)
        sa.Column('metadata', postgresql.JSONB(asdict=False), nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['parent_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['asset_templates.id'], ondelete='SET NULL'),
    )

    # Create indexes for assets
    op.create_index('ix_assets_name', 'assets', ['name'])
    op.create_index('ix_assets_asset_type', 'assets', ['asset_type'])
    op.create_index('ix_assets_parent_id', 'assets', ['parent_id'])
    op.create_index('ix_assets_template_id', 'assets', ['template_id'])

    # Create asset_attributes table
    op.create_table(
        'asset_attributes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Attribute info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Attribute type
        sa.Column('attribute_type', sa.Enum(
            'tag_reference', 'static', 'calculated',
            name='asset_attribute_type',
            create_type=True
        ), nullable=False, server_default='tag_reference'),

        # For TAG_REFERENCE type
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=True),

        # For STATIC type
        sa.Column('static_value', sa.String(500), nullable=True),

        # For CALCULATED type
        sa.Column('formula', sa.Text(), nullable=True),

        # Unit of measure
        sa.Column('unit', sa.String(50), nullable=True),

        # Display order
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),

        # Additional settings
        sa.Column('settings', postgresql.JSONB(asdict=False), nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='SET NULL'),
    )

    # Create indexes for asset_attributes
    op.create_index('ix_asset_attributes_asset_id', 'asset_attributes', ['asset_id'])
    op.create_index('ix_asset_attributes_name', 'asset_attributes', ['name'])
    op.create_index('ix_asset_attributes_tag_id', 'asset_attributes', ['tag_id'])


def downgrade():
    # Drop tables in reverse order (dependencies first)

    # Drop asset_attributes indexes and table
    op.drop_index('ix_asset_attributes_tag_id', table_name='asset_attributes')
    op.drop_index('ix_asset_attributes_name', table_name='asset_attributes')
    op.drop_index('ix_asset_attributes_asset_id', table_name='asset_attributes')
    op.drop_table('asset_attributes')

    # Drop asset_attribute_type enum
    op.execute('DROP TYPE asset_attribute_type')

    # Drop assets indexes and table
    op.drop_index('ix_assets_template_id', table_name='assets')
    op.drop_index('ix_assets_parent_id', table_name='assets')
    op.drop_index('ix_assets_asset_type', table_name='assets')
    op.drop_index('ix_assets_name', table_name='assets')
    op.drop_table('assets')

    # Drop asset_templates indexes and table
    op.drop_index('ix_asset_templates_asset_type', table_name='asset_templates')
    op.drop_index('ix_asset_templates_name', table_name='asset_templates')
    op.drop_table('asset_templates')

    # Drop assettype enum
    op.execute('DROP TYPE assettype')
