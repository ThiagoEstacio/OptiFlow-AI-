-- Migration: Add Extended Tags and Formulas for PI Asset Framework features
-- Created: 2025-11-04

-- Add missing columns to assets table
ALTER TABLE assets ADD COLUMN IF NOT EXISTS path VARCHAR(1000);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 0;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS icon VARCHAR(100);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS color VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_assets_path_new ON assets(path);

-- Update existing assets with paths (if they don't have them)
UPDATE assets SET path = '/' || name WHERE path IS NULL AND parent_id IS NULL;

-- Create extended tags table with all PI AF features
CREATE TABLE IF NOT EXISTS gateway_tags_extended (
    id SERIAL PRIMARY KEY,
    gateway_id INTEGER REFERENCES gateway_configs(id) ON DELETE CASCADE,
    tag_name VARCHAR(200) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Hierarchy
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
    tag_group VARCHAR(200),

    -- Tag type
    tag_type VARCHAR(50) DEFAULT 'physical' NOT NULL CHECK (tag_type IN ('physical', 'calculated', 'logical', 'aggregated')),

    -- Physical tag fields
    address_config JSONB,
    data_type VARCHAR(50) DEFAULT 'float',
    scale_factor DOUBLE PRECISION DEFAULT 1.0,
    tag_offset DOUBLE PRECISION DEFAULT 0.0,  -- renamed from 'offset' which is reserved

    -- Calculated/logical tag fields
    formula TEXT,
    formula_tags JSONB,
    condition TEXT,

    -- Units and limits
    unit VARCHAR(50),
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,

    -- Historical archiving (PI-style)
    archive_enabled BOOLEAN DEFAULT TRUE,
    archive_type VARCHAR(50) DEFAULT 'on_change',
    archive_deadband DOUBLE PRECISION,
    archive_interval_seconds INTEGER,
    compression_deviation DOUBLE PRECISION,

    -- Quality and alarms
    quality_enabled BOOLEAN DEFAULT TRUE,
    alarm_enabled BOOLEAN DEFAULT FALSE,
    alarm_config JSONB,

    -- Metadata
    description VARCHAR(1000),
    category VARCHAR(100),
    properties JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_gateway_tags_ext_gateway ON gateway_tags_extended(gateway_id);
CREATE INDEX IF NOT EXISTS idx_gateway_tags_ext_asset ON gateway_tags_extended(asset_id);
CREATE INDEX IF NOT EXISTS idx_gateway_tags_ext_name ON gateway_tags_extended(tag_name);
CREATE INDEX IF NOT EXISTS idx_gateway_tags_ext_type ON gateway_tags_extended(tag_type);
CREATE INDEX IF NOT EXISTS idx_gateway_tags_ext_enabled ON gateway_tags_extended(enabled);

-- Create tag formulas table
CREATE TABLE IF NOT EXISTS tag_formulas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description VARCHAR(1000),

    -- Formula definition
    formula_type VARCHAR(50) NOT NULL,
    expression TEXT NOT NULL,

    -- Input/Output
    input_tags JSONB,
    output_unit VARCHAR(50),
    output_type VARCHAR(50),

    -- Execution
    execution_interval_seconds INTEGER,
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    category VARCHAR(100),
    tags_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_tag_formulas_name ON tag_formulas(name);
CREATE INDEX IF NOT EXISTS idx_tag_formulas_type ON tag_formulas(formula_type);
CREATE INDEX IF NOT EXISTS idx_tag_formulas_active ON tag_formulas(is_active);

-- Create trigger for gateway_tags_extended updated_at
DROP TRIGGER IF EXISTS update_gateway_tags_ext_updated_at ON gateway_tags_extended;
CREATE TRIGGER update_gateway_tags_ext_updated_at BEFORE UPDATE ON gateway_tags_extended
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for tag_formulas updated_at
DROP TRIGGER IF EXISTS update_tag_formulas_updated_at ON tag_formulas;
CREATE TRIGGER update_tag_formulas_updated_at BEFORE UPDATE ON tag_formulas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Display summary
SELECT 'Migration completed successfully!' as status;
