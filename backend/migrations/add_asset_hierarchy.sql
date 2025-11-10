-- Migration: Add Asset Hierarchy and Extended Tags (PI Asset Framework style)
-- Created: 2025-11-04

-- Create asset hierarchy table
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('site', 'area', 'unit', 'equipment', 'tag_group')),
    parent_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    path VARCHAR(1000),
    level INTEGER DEFAULT 0,
    description VARCHAR(1000),
    properties JSONB,
    icon VARCHAR(100),
    color VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT assets_name_parent_unique UNIQUE (name, parent_id)
);

CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_parent ON assets(parent_id);
CREATE INDEX idx_assets_path ON assets(path);
CREATE INDEX idx_assets_name ON assets(name);

-- Create extended tags table
CREATE TABLE IF NOT EXISTS gateway_tags_extended (
    id SERIAL PRIMARY KEY,
    gateway_id INTEGER REFERENCES gateway_configs(id) ON DELETE CASCADE,
    tag_name VARCHAR(200) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Hierarchy
    asset_id INTEGER REFERENCES assets(id) ON DELETE SET NULL,
    tag_group VARCHAR(200),

    -- Tag type
    tag_type VARCHAR(50) DEFAULT 'physical' NOT NULL CHECK (tag_type IN ('physical', 'calculated', 'logical', 'aggregated')),

    -- Physical tag fields
    address_config JSONB,
    data_type VARCHAR(50) DEFAULT 'float',
    scale_factor DOUBLE PRECISION DEFAULT 1.0,
    offset DOUBLE PRECISION DEFAULT 0.0,

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

CREATE INDEX idx_gateway_tags_ext_gateway ON gateway_tags_extended(gateway_id);
CREATE INDEX idx_gateway_tags_ext_asset ON gateway_tags_extended(asset_id);
CREATE INDEX idx_gateway_tags_ext_name ON gateway_tags_extended(tag_name);
CREATE INDEX idx_gateway_tags_ext_type ON gateway_tags_extended(tag_type);
CREATE INDEX idx_gateway_tags_ext_enabled ON gateway_tags_extended(enabled);

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

CREATE INDEX idx_tag_formulas_name ON tag_formulas(name);
CREATE INDEX idx_tag_formulas_type ON tag_formulas(formula_type);
CREATE INDEX idx_tag_formulas_active ON tag_formulas(is_active);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gateway_tags_ext_updated_at BEFORE UPDATE ON gateway_tags_extended
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tag_formulas_updated_at BEFORE UPDATE ON tag_formulas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample hierarchy
INSERT INTO assets (name, asset_type, parent_id, path, level, description, icon, color) VALUES
('OptiFlow Plant', 'site', NULL, '/OptiFlow Plant', 0, 'Main industrial plant', 'factory', '#1976D2'),
('Production Area 1', 'area', 1, '/OptiFlow Plant/Production Area 1', 1, 'Primary production area', 'warehouse', '#43A047'),
('Conveyor System', 'unit', 2, '/OptiFlow Plant/Production Area 1/Conveyor System', 2, 'Belt conveyor system', 'conveyor', '#F57C00')
ON CONFLICT DO NOTHING;

COMMIT;

-- Display summary
SELECT
    'Assets created:' as info,
    COUNT(*) as count
FROM assets
UNION ALL
SELECT
    'Extended tags structure ready:' as info,
    0 as count;
