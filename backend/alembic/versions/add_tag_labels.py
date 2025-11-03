"""add_tag_labels_table

Revision ID: add_tag_labels
Revises: previous_migration
Create Date: 2025-11-02 21:30:00.000000

Creates tag_labels table for user-friendly tag aliases and organization
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_tag_labels'
down_revision = None  # Update this to match your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create tag_labels table
    op.create_table(
        'tag_labels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # User-friendly identifiers
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('short_name', sa.String(100), nullable=True),
        
        # Organization
        sa.Column('equipment_name', sa.String(255), nullable=True),
        sa.Column('area_name', sa.String(255), nullable=True),
        sa.Column('system_name', sa.String(255), nullable=True),
        
        # Custom description
        sa.Column('custom_description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Visibility
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'),
        
        # Audit
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Foreign key
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_tag_labels_tag_id', 'tag_labels', ['tag_id'], unique=True)
    op.create_index('ix_tag_labels_display_name', 'tag_labels', ['display_name'])
    op.create_index('ix_tag_labels_equipment_name', 'tag_labels', ['equipment_name'])
    op.create_index('ix_tag_labels_area_name', 'tag_labels', ['area_name'])
    op.create_index('ix_tag_labels_system_name', 'tag_labels', ['system_name'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_tag_labels_system_name', table_name='tag_labels')
    op.drop_index('ix_tag_labels_area_name', table_name='tag_labels')
    op.drop_index('ix_tag_labels_equipment_name', table_name='tag_labels')
    op.drop_index('ix_tag_labels_display_name', table_name='tag_labels')
    op.drop_index('ix_tag_labels_tag_id', table_name='tag_labels')
    
    # Drop table
    op.drop_table('tag_labels')
