#!/bin/bash
# Initialize PostgreSQL Primary for Replication
# =============================================

set -e

# Create replication user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create replication user
    CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD '${POSTGRES_REPLICATION_PASSWORD:-replication_password}';

    -- Create replication slot for each replica
    SELECT pg_create_physical_replication_slot('replica_1_slot');
    SELECT pg_create_physical_replication_slot('replica_2_slot');

    -- Grant necessary permissions
    GRANT CONNECT ON DATABASE optiflow TO replicator;

    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Create monitoring schema
    CREATE SCHEMA IF NOT EXISTS monitoring;

    -- Create replication monitoring view
    CREATE OR REPLACE VIEW monitoring.replication_status AS
    SELECT
        client_addr,
        state,
        sent_lsn,
        write_lsn,
        flush_lsn,
        replay_lsn,
        write_lag,
        flush_lag,
        replay_lag,
        sync_state
    FROM pg_stat_replication;

    -- Create database stats view
    CREATE OR REPLACE VIEW monitoring.database_stats AS
    SELECT
        datname,
        numbackends,
        xact_commit,
        xact_rollback,
        blks_read,
        blks_hit,
        ROUND(100.0 * blks_hit / NULLIF(blks_read + blks_hit, 0), 2) AS cache_hit_ratio,
        tup_returned,
        tup_fetched,
        tup_inserted,
        tup_updated,
        tup_deleted,
        conflicts,
        temp_files,
        temp_bytes,
        deadlocks
    FROM pg_stat_database
    WHERE datname = 'optiflow';

    -- Log completion
    \echo 'Primary database initialized for replication'
EOSQL

echo "Primary database initialization complete!"
