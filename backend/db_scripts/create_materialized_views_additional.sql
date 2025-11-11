-- ========================================
-- MATERIALIZED VIEWS ADICIONAIS
-- OptiFlow AI - Assets, Alarms, Tags Performance
-- ========================================

-- ============================================================================
-- 1. ASSET HEALTH OVERVIEW
-- Pre-calculate asset health scores for fast dashboard loading
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_asset_health_overview CASCADE;

CREATE MATERIALIZED VIEW mv_asset_health_overview AS
SELECT 
    a.id as asset_id,
    a.name as asset_name,
    a.asset_type,
    a.site_id,
    a.status,
    -- Health metrics
    CASE 
        WHEN a.status = 'OPERATIONAL' THEN 95.0
        WHEN a.status = 'WARNING' THEN 75.0
        WHEN a.status = 'ALARM' THEN 50.0
        WHEN a.status = 'MAINTENANCE' THEN 30.0
        ELSE 0.0
    END as health_score,
    -- Aggregate attribute counts
    COUNT(DISTINCT aa.id) as total_attributes,
    COUNT(DISTINCT aa.id) FILTER (WHERE aa.value::float > 0) as active_attributes,
    -- Timestamps
    a.last_maintenance,
    a.updated_at as last_updated,
    CURRENT_TIMESTAMP as view_refreshed_at
FROM assets a
LEFT JOIN asset_attributes aa ON a.id = aa.asset_id
GROUP BY a.id, a.name, a.asset_type, a.site_id, a.status, a.last_maintenance, a.updated_at;

-- Indexes for fast lookups
CREATE INDEX idx_mv_asset_health_score ON mv_asset_health_overview(health_score DESC);
CREATE INDEX idx_mv_asset_site ON mv_asset_health_overview(site_id, asset_type);
CREATE INDEX idx_mv_asset_status ON mv_asset_health_overview(status, health_score DESC);

COMMENT ON MATERIALIZED VIEW mv_asset_health_overview IS 
'Pre-calculated asset health scores. Refresh every 5 minutes. Expected: -60% query time on asset dashboards.';

-- ============================================================================
-- 2. ALARM STATISTICS
-- Daily alarm aggregations for trends and analytics
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_alarm_statistics CASCADE;

CREATE MATERIALIZED VIEW mv_alarm_statistics AS
SELECT 
    DATE_TRUNC('day', ae.trigger_timestamp) as alarm_date,
    ad.tag_id,
    t.name as tag_name,
    t.device_id,
    d.name as device_name,
    -- Alarm counts by severity
    COUNT(*) as total_alarms,
    COUNT(*) FILTER (WHERE ad.severity = 'CRITICAL') as critical_alarms,
    COUNT(*) FILTER (WHERE ad.severity = 'HIGH') as high_alarms,
    COUNT(*) FILTER (WHERE ad.severity = 'MEDIUM') as medium_alarms,
    COUNT(*) FILTER (WHERE ad.severity = 'LOW') as low_alarms,
    -- Alarm states
    COUNT(*) FILTER (WHERE ae.state = 'ACTIVE') as active_alarms,
    COUNT(*) FILTER (WHERE ae.state = 'ACKNOWLEDGED') as acknowledged_alarms,
    COUNT(*) FILTER (WHERE ae.state = 'CLEARED') as cleared_alarms,
    -- Performance metrics
    AVG(ae.duration_seconds) as avg_duration_seconds,
    MAX(ae.duration_seconds) as max_duration_seconds,
    MIN(ae.duration_seconds) as min_duration_seconds,
    -- Response times
    AVG(EXTRACT(EPOCH FROM (ae.acknowledged_at - ae.trigger_timestamp))) 
        FILTER (WHERE ae.acknowledged_at IS NOT NULL) as avg_acknowledge_time_seconds,
    AVG(EXTRACT(EPOCH FROM (ae.cleared_at - ae.trigger_timestamp))) 
        FILTER (WHERE ae.cleared_at IS NOT NULL) as avg_clear_time_seconds,
    -- Metadata
    CURRENT_TIMESTAMP as view_refreshed_at
FROM alarm_events ae
JOIN alarm_definitions ad ON ae.definition_id = ad.id
JOIN tags t ON ad.tag_id = t.id
JOIN devices d ON t.device_id = d.id
WHERE ae.trigger_timestamp IS NOT NULL
GROUP BY 
    DATE_TRUNC('day', ae.trigger_timestamp),
    ad.tag_id,
    t.name,
    t.device_id,
    d.name;

-- Indexes for fast filtering
CREATE INDEX idx_mv_alarm_stats_date ON mv_alarm_statistics(alarm_date DESC);
CREATE INDEX idx_mv_alarm_stats_tag ON mv_alarm_statistics(tag_id, alarm_date DESC);
CREATE INDEX idx_mv_alarm_stats_device ON mv_alarm_statistics(device_id, alarm_date DESC);
CREATE INDEX idx_mv_alarm_stats_critical ON mv_alarm_statistics(critical_alarms DESC) WHERE critical_alarms > 0;

COMMENT ON MATERIALIZED VIEW mv_alarm_statistics IS 
'Daily alarm aggregations by tag/device. Refresh every 1 hour. Expected: -70% query time on alarm trends.';

-- ============================================================================
-- 3. TAG PERFORMANCE METRICS
-- Quality and performance metrics per tag
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_tag_performance CASCADE;

CREATE MATERIALIZED VIEW mv_tag_performance AS
SELECT 
    t.id as tag_id,
    t.name as tag_name,
    t.device_id,
    d.name as device_name,
    t.category,
    t.data_type,
    t.is_active,
    -- Performance metrics
    t.data_points_count,
    t.scan_rate_ms,
    -- Quality indicators
    CASE 
        WHEN t.last_quality IS NULL THEN 'NEVER_READ'
        WHEN t.last_quality = 'GOOD' THEN 'GOOD'
        WHEN t.last_quality = 'BAD' THEN 'BAD'
        ELSE 'UNCERTAIN'
    END as quality_status,
    -- Timing
    t.last_timestamp,
    CASE 
        WHEN t.last_timestamp IS NULL THEN NULL
        WHEN t.last_timestamp < CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 'STALE'
        WHEN t.last_timestamp < CURRENT_TIMESTAMP - INTERVAL '10 minutes' THEN 'WARNING'
        ELSE 'FRESH'
    END as data_freshness,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - t.last_timestamp)) / 60 as minutes_since_last_update,
    -- Configuration
    t.min_value,
    t.max_value,
    t.engineering_min,
    t.engineering_max,
    t.unit,
    -- Metadata
    t.created_at,
    t.updated_at,
    CURRENT_TIMESTAMP as view_refreshed_at
FROM tags t
JOIN devices d ON t.device_id = d.id;

-- Indexes for fast filtering
CREATE INDEX idx_mv_tag_perf_device ON mv_tag_performance(device_id, is_active);
CREATE INDEX idx_mv_tag_perf_category ON mv_tag_performance(category, is_active);
CREATE INDEX idx_mv_tag_perf_quality ON mv_tag_performance(quality_status, data_freshness);
CREATE INDEX idx_mv_tag_perf_stale ON mv_tag_performance(minutes_since_last_update DESC NULLS LAST) 
    WHERE is_active = true;
CREATE INDEX idx_mv_tag_perf_datapoints ON mv_tag_performance(data_points_count DESC);

COMMENT ON MATERIALIZED VIEW mv_tag_performance IS 
'Tag quality and performance metrics. Refresh every 2 minutes. Expected: -65% query time on tag health dashboards.';

-- ============================================================================
-- REFRESH FUNCTIONS
-- ============================================================================

-- Function to refresh asset health
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

-- ============================================================================
-- INITIAL REFRESH
-- ============================================================================

REFRESH MATERIALIZED VIEW mv_asset_health_overview;
REFRESH MATERIALIZED VIEW mv_alarm_statistics;
REFRESH MATERIALIZED VIEW mv_tag_performance;

-- ============================================================================
-- SUMMARY
-- ============================================================================

SELECT 
    'mv_asset_health_overview' as view_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('mv_asset_health_overview')) as size
FROM mv_asset_health_overview
UNION ALL
SELECT 
    'mv_alarm_statistics' as view_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('mv_alarm_statistics')) as size
FROM mv_alarm_statistics
UNION ALL
SELECT 
    'mv_tag_performance' as view_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('mv_tag_performance')) as size
FROM mv_tag_performance;

-- ============================================================================
-- EXPECTED IMPROVEMENTS
-- ============================================================================
-- ✅ Asset health dashboard: -60% query time
-- ✅ Alarm trends dashboard: -70% query time
-- ✅ Tag health monitoring: -65% query time
-- ✅ Overall: -65% average query time on analytics dashboards
-- ✅ Refresh schedule: 
--    - mv_asset_health_overview: Every 5 minutes
--    - mv_alarm_statistics: Every 1 hour
--    - mv_tag_performance: Every 2 minutes
