-- ========================================
-- AUTO-REFRESH MATERIALIZED VIEWS
-- OptiFlow AI - PostgreSQL pg_cron Setup
-- ========================================

-- ============================================================================
-- 1. INSTALL PG_CRON EXTENSION
-- ============================================================================

-- Check if pg_cron is available
SELECT * FROM pg_available_extensions WHERE name = 'pg_cron';

-- Install pg_cron (requires superuser)
-- Note: On some systems, pg_cron needs to be added to shared_preload_libraries
-- and PostgreSQL restarted before this works
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Grant permissions to optiflow user
GRANT USAGE ON SCHEMA cron TO optiflow;

-- ============================================================================
-- 2. SCHEDULE MATERIALIZED VIEW REFRESHES
-- ============================================================================

-- Delete existing schedules if they exist (idempotent)
SELECT cron.unschedule(jobid) 
FROM cron.job 
WHERE jobname IN (
    'refresh-alarm-stats',
    'refresh-tag-performance', 
    'refresh-asset-health',
    'refresh-operations-summary'
);

-- ============================================================================
-- Schedule 1: Alarm Statistics (Every 1 hour)
-- ============================================================================
SELECT cron.schedule(
    'refresh-alarm-stats',          -- Job name
    '0 * * * *',                     -- Cron: Every hour at minute 0
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_alarm_statistics$$
);

COMMENT ON EXTENSION pg_cron IS 
'Auto-refresh alarm statistics: Every 1 hour. Expected -70% query time on alarm trends.';

-- ============================================================================
-- Schedule 2: Tag Performance (Every 2 minutes)
-- ============================================================================
SELECT cron.schedule(
    'refresh-tag-performance',       -- Job name
    '*/2 * * * *',                   -- Cron: Every 2 minutes
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tag_performance$$
);

COMMENT ON EXTENSION pg_cron IS 
'Auto-refresh tag performance: Every 2 minutes. Expected -65% query time on tag health dashboards.';

-- ============================================================================
-- Schedule 3: Asset Health Overview (Every 5 minutes)
-- ============================================================================
SELECT cron.schedule(
    'refresh-asset-health',          -- Job name
    '*/5 * * * *',                   -- Cron: Every 5 minutes
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_asset_health_overview$$
);

COMMENT ON EXTENSION pg_cron IS 
'Auto-refresh asset health: Every 5 minutes. Expected -60% query time on asset dashboards.';

-- ============================================================================
-- Schedule 4: Daily Operations Summary (Every 1 hour)
-- ============================================================================
SELECT cron.schedule(
    'refresh-operations-summary',    -- Job name
    '0 * * * *',                     -- Cron: Every hour at minute 0
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_operations_summary$$
);

COMMENT ON EXTENSION pg_cron IS 
'Auto-refresh operations summary: Every 1 hour. Expected -84% query time on operations dashboard.';

-- ============================================================================
-- 3. VERIFY SCHEDULES
-- ============================================================================

SELECT 
    jobid,
    schedule,
    command,
    nodename,
    nodeport,
    database,
    username,
    active,
    jobname
FROM cron.job
ORDER BY jobname;

-- ============================================================================
-- 4. CHECK EXECUTION HISTORY
-- ============================================================================

-- View recent job runs
SELECT 
    jobid,
    runid,
    job_pid,
    database,
    username,
    command,
    status,
    return_message,
    start_time,
    end_time,
    EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds
FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 20;

-- ============================================================================
-- 5. MONITORING QUERIES
-- ============================================================================

-- Check if jobs are running
SELECT 
    j.jobname,
    j.schedule,
    j.active,
    COUNT(r.runid) as total_runs,
    COUNT(r.runid) FILTER (WHERE r.status = 'succeeded') as successful_runs,
    COUNT(r.runid) FILTER (WHERE r.status = 'failed') as failed_runs,
    MAX(r.end_time) as last_run,
    AVG(EXTRACT(EPOCH FROM (r.end_time - r.start_time))) as avg_duration_seconds
FROM cron.job j
LEFT JOIN cron.job_run_details r ON j.jobid = r.jobid
WHERE j.jobname LIKE 'refresh-%'
GROUP BY j.jobid, j.jobname, j.schedule, j.active
ORDER BY j.jobname;

-- ============================================================================
-- 6. MANUAL REFRESH (if needed)
-- ============================================================================

-- Manually trigger refreshes if needed
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_alarm_statistics;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tag_performance;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_asset_health_overview;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_operations_summary;

-- ============================================================================
-- 7. DISABLE/ENABLE SCHEDULES (if needed)
-- ============================================================================

-- Disable a specific job
-- UPDATE cron.job SET active = false WHERE jobname = 'refresh-alarm-stats';

-- Enable a specific job
-- UPDATE cron.job SET active = true WHERE jobname = 'refresh-alarm-stats';

-- ============================================================================
-- EXPECTED RESULTS
-- ============================================================================
-- ✅ 4 materialized views auto-refreshing
-- ✅ mv_alarm_statistics: Every 1 hour
-- ✅ mv_tag_performance: Every 2 minutes
-- ✅ mv_asset_health_overview: Every 5 minutes  
-- ✅ mv_daily_operations_summary: Every 1 hour
-- ✅ Zero manual intervention required
-- ✅ Dashboard queries always have fresh data
-- ✅ -65% average query time maintained

-- ============================================================================
-- TROUBLESHOOTING
-- ============================================================================

-- If pg_cron extension fails to install:
-- 1. Check if pg_cron is installed on system:
--    apt-get install postgresql-15-cron (Ubuntu/Debian)
--    yum install pg_cron_15 (CentOS/RHEL)
--
-- 2. Add to postgresql.conf:
--    shared_preload_libraries = 'pg_cron'
--    cron.database_name = 'optiflow'
--
-- 3. Restart PostgreSQL:
--    docker compose restart postgres

-- If schedules don't run:
-- 1. Check if pg_cron background worker is running:
SELECT * FROM pg_stat_activity WHERE backend_type = 'pg_cron launcher';

-- 2. Check logs:
SELECT * FROM cron.job_run_details WHERE status = 'failed' ORDER BY start_time DESC LIMIT 10;

-- 3. Verify permissions:
SELECT * FROM information_schema.role_table_grants 
WHERE grantee = 'optiflow' AND table_name LIKE 'mv_%';
