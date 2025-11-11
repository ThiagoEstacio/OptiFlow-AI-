-- ==================================================================
-- MATERIALIZED VIEWS ADICIONAIS - OPTIFLOW
-- ==================================================================
-- Criado: 2025-11-11
-- Propósito: Otimizar queries de assets, alarms e tags
-- Ganho esperado: -60% query time em endpoints críticos
-- ==================================================================

-- ==================================================================
-- 1. ASSET HEALTH OVERVIEW MATERIALIZED VIEW
-- ==================================================================
-- Pré-calcula health scores e estatísticas de assets

DROP MATERIALIZED VIEW IF EXISTS mv_asset_health_overview CASCADE;

CREATE MATERIALIZED VIEW mv_asset_health_overview AS
SELECT 
    a.id as asset_id,
    a.name as asset_name,
    a.asset_type,
    a.site_id,
    
    -- Health Score Aggregations
    COUNT(ahh.id) as health_records_count,
    AVG(ahh.health_score) as avg_health_score,
    MIN(ahh.health_score) as min_health_score,
    MAX(ahh.health_score) as max_health_score,
    STDDEV(ahh.health_score) as stddev_health_score,
    
    -- Latest Health Status
    (SELECT health_score 
     FROM asset_health_history 
     WHERE asset_id = a.id 
     ORDER BY recorded_at DESC 
     LIMIT 1) as latest_health_score,
    
    (SELECT recorded_at 
     FROM asset_health_history 
     WHERE asset_id = a.id 
     ORDER BY recorded_at DESC 
     LIMIT 1) as latest_health_timestamp,
    
    -- Active Alerts Count
    (SELECT COUNT(*) 
     FROM asset_health_alerts 
     WHERE asset_id = a.id 
     AND resolved_at IS NULL) as active_alerts_count,
    
    -- Criticality Indicators
    COUNT(*) FILTER (WHERE ahh.health_score < 50) as critical_readings_count,
    COUNT(*) FILTER (WHERE ahh.health_score < 70) as warning_readings_count,
    COUNT(*) FILTER (WHERE ahh.health_score >= 70) as healthy_readings_count,
    
    -- Time Ranges
    MIN(ahh.recorded_at) as first_reading_at,
    MAX(ahh.recorded_at) as last_reading_at,
    
    -- Asset Metadata
    a.status as asset_status,
    a.created_at as asset_created_at,
    a.updated_at as asset_updated_at

FROM assets a
LEFT JOIN asset_health_history ahh ON a.id = ahh.asset_id
GROUP BY a.id, a.name, a.asset_type, a.site_id, a.status, a.created_at, a.updated_at;

-- Indexes for fast lookups
CREATE INDEX idx_mv_asset_health_asset_id ON mv_asset_health_overview(asset_id);
CREATE INDEX idx_mv_asset_health_score ON mv_asset_health_overview(avg_health_score DESC);
CREATE INDEX idx_mv_asset_health_site ON mv_asset_health_overview(site_id);
CREATE INDEX idx_mv_asset_health_type ON mv_asset_health_overview(asset_type);
CREATE INDEX idx_mv_asset_health_alerts ON mv_asset_health_overview(active_alerts_count DESC);

COMMENT ON MATERIALIZED VIEW mv_asset_health_overview IS 
'Pré-calcula métricas de saúde de assets. Atualizar a cada 15 minutos.';

-- ==================================================================
-- 2. ALARM STATISTICS MATERIALIZED VIEW
-- ==================================================================
-- Pré-calcula estatísticas de alarmes por definição e site

DROP MATERIALIZED VIEW IF EXISTS mv_alarm_statistics CASCADE;

CREATE MATERIALIZED VIEW mv_alarm_statistics AS
SELECT 
    ad.id as alarm_definition_id,
    ad.name as alarm_name,
    ad.priority as alarm_priority,
    ad.site_id,
    
    -- Event Counts
    COUNT(ae.id) as total_events,
    COUNT(*) FILTER (WHERE ae.acknowledged_at IS NOT NULL) as acknowledged_count,
    COUNT(*) FILTER (WHERE ae.resolved_at IS NOT NULL) as resolved_count,
    COUNT(*) FILTER (WHERE ae.acknowledged_at IS NULL AND ae.resolved_at IS NULL) as active_count,
    
    -- Time Statistics (in seconds)
    AVG(EXTRACT(EPOCH FROM (ae.acknowledged_at - ae.occurred_at))) FILTER (WHERE ae.acknowledged_at IS NOT NULL) 
        as avg_acknowledgment_time_seconds,
    AVG(EXTRACT(EPOCH FROM (ae.resolved_at - ae.occurred_at))) FILTER (WHERE ae.resolved_at IS NOT NULL) 
        as avg_resolution_time_seconds,
    
    MIN(EXTRACT(EPOCH FROM (ae.acknowledged_at - ae.occurred_at))) FILTER (WHERE ae.acknowledged_at IS NOT NULL) 
        as min_acknowledgment_time_seconds,
    MAX(EXTRACT(EPOCH FROM (ae.acknowledged_at - ae.occurred_at))) FILTER (WHERE ae.acknowledged_at IS NOT NULL) 
        as max_acknowledgment_time_seconds,
    
    MIN(EXTRACT(EPOCH FROM (ae.resolved_at - ae.occurred_at))) FILTER (WHERE ae.resolved_at IS NOT NULL) 
        as min_resolution_time_seconds,
    MAX(EXTRACT(EPOCH FROM (ae.resolved_at - ae.occurred_at))) FILTER (WHERE ae.resolved_at IS NOT NULL) 
        as max_resolution_time_seconds,
    
    -- Recent Activity (last 24h, 7d, 30d)
    COUNT(*) FILTER (WHERE ae.occurred_at > NOW() - INTERVAL '24 hours') as events_last_24h,
    COUNT(*) FILTER (WHERE ae.occurred_at > NOW() - INTERVAL '7 days') as events_last_7d,
    COUNT(*) FILTER (WHERE ae.occurred_at > NOW() - INTERVAL '30 days') as events_last_30d,
    
    -- Time Ranges
    MIN(ae.occurred_at) as first_event_at,
    MAX(ae.occurred_at) as last_event_at,
    
    -- Alarm Definition Metadata
    ad.enabled as alarm_enabled,
    ad.created_at as alarm_created_at

FROM alarm_definitions ad
LEFT JOIN alarm_events ae ON ad.id = ae.alarm_definition_id
GROUP BY ad.id, ad.name, ad.priority, ad.site_id, ad.enabled, ad.created_at;

-- Indexes for fast lookups
CREATE INDEX idx_mv_alarm_stats_def_id ON mv_alarm_statistics(alarm_definition_id);
CREATE INDEX idx_mv_alarm_stats_site ON mv_alarm_statistics(site_id);
CREATE INDEX idx_mv_alarm_stats_priority ON mv_alarm_statistics(alarm_priority);
CREATE INDEX idx_mv_alarm_stats_active ON mv_alarm_statistics(active_count DESC);
CREATE INDEX idx_mv_alarm_stats_total ON mv_alarm_statistics(total_events DESC);

COMMENT ON MATERIALIZED VIEW mv_alarm_statistics IS 
'Pré-calcula estatísticas de alarmes por definição. Atualizar a cada 5 minutos.';

-- ==================================================================
-- 3. TAG PERFORMANCE MATERIALIZED VIEW
-- ==================================================================
-- Pré-calcula métricas de qualidade e performance de tags

DROP MATERIALIZED VIEW IF EXISTS mv_tag_performance CASCADE;

CREATE MATERIALIZED VIEW mv_tag_performance AS
SELECT 
    gt.id as tag_id,
    gt.name as tag_name,
    gt.device_id,
    gt.site_id,
    gt.data_type,
    
    -- Tag Metadata
    gt.unit,
    gt.description,
    gt.min_value,
    gt.max_value,
    gt.scaling_factor,
    
    -- Configuration Status
    gt.enabled as tag_enabled,
    gt.logging_enabled,
    gt.alarm_enabled,
    
    -- Quality Indicators (derived from related tables)
    CASE 
        WHEN gt.enabled THEN 'ACTIVE'
        ELSE 'INACTIVE'
    END as operational_status,
    
    -- Device Association
    d.name as device_name,
    d.status as device_status,
    
    -- Extended Attributes (if available)
    gte.read_rate_ms as polling_rate,
    gte.last_good_value,
    gte.last_update_time,
    
    -- Alarm Configuration
    COUNT(ad.id) as associated_alarms_count,
    COUNT(*) FILTER (WHERE ad.enabled = true) as active_alarms_count,
    
    -- Time Metadata
    gt.created_at as tag_created_at,
    gt.updated_at as tag_updated_at

FROM gateway_tags gt
LEFT JOIN devices d ON gt.device_id = d.id
LEFT JOIN gateway_tags_extended gte ON gt.id = gte.tag_id
LEFT JOIN alarm_definitions ad ON ad.tag_id = gt.id
GROUP BY 
    gt.id, gt.name, gt.device_id, gt.site_id, gt.data_type,
    gt.unit, gt.description, gt.min_value, gt.max_value, gt.scaling_factor,
    gt.enabled, gt.logging_enabled, gt.alarm_enabled,
    d.name, d.status,
    gte.read_rate_ms, gte.last_good_value, gte.last_update_time,
    gt.created_at, gt.updated_at;

-- Indexes for fast lookups
CREATE INDEX idx_mv_tag_perf_tag_id ON mv_tag_performance(tag_id);
CREATE INDEX idx_mv_tag_perf_name ON mv_tag_performance(tag_name);
CREATE INDEX idx_mv_tag_perf_device ON mv_tag_performance(device_id);
CREATE INDEX idx_mv_tag_perf_site ON mv_tag_performance(site_id);
CREATE INDEX idx_mv_tag_perf_enabled ON mv_tag_performance(tag_enabled);
CREATE INDEX idx_mv_tag_perf_status ON mv_tag_performance(operational_status);

COMMENT ON MATERIALIZED VIEW mv_tag_performance IS 
'Pré-calcula métricas de performance e qualidade de tags. Atualizar a cada 10 minutos.';

-- ==================================================================
-- REFRESH FUNCTIONS
-- ==================================================================

-- Function to refresh asset health overview
CREATE OR REPLACE FUNCTION refresh_asset_health_view()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_asset_health_overview;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh alarm statistics
CREATE OR REPLACE FUNCTION refresh_alarm_statistics_view()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_alarm_statistics;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh tag performance
CREATE OR REPLACE FUNCTION refresh_tag_performance_view()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tag_performance;
END;
$$ LANGUAGE plpgsql;

-- Initial refresh
REFRESH MATERIALIZED VIEW mv_asset_health_overview;
REFRESH MATERIALIZED VIEW mv_alarm_statistics;
REFRESH MATERIALIZED VIEW mv_tag_performance;

-- ==================================================================
-- VERIFICATION QUERIES
-- ==================================================================

SELECT 'mv_asset_health_overview' as view_name, COUNT(*) as record_count FROM mv_asset_health_overview
UNION ALL
SELECT 'mv_alarm_statistics' as view_name, COUNT(*) as record_count FROM mv_alarm_statistics
UNION ALL
SELECT 'mv_tag_performance' as view_name, COUNT(*) as record_count FROM mv_tag_performance;
