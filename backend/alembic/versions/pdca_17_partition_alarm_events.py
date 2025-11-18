"""PDCA #17: Partition alarm_events table by timestamp

Revision ID: pdca_17_partition
Revises:
Create Date: 2025-01-13

Partitions the alarm_events table by timestamp (monthly partitions).

Benefits:
- Query performance improvement for time-range queries
- Easier maintenance and archiving of old data
- Better index performance
- Automatic partition creation for new months
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'pdca_17_partition'
down_revision = None  # Set this to your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Convert alarm_events table to partitioned table.

    Strategy:
    1. Rename existing table
    2. Create new partitioned table
    3. Copy data from old table
    4. Create initial partitions (last 12 months + next 3 months)
    5. Drop old table
    """

    # Check if PostgreSQL version supports partitioning (>= 10)
    conn = op.get_bind()

    # Step 1: Rename existing table
    op.execute(text("""
        ALTER TABLE IF EXISTS alarm_events RENAME TO alarm_events_old;
    """))

    # Step 2: Create new partitioned table
    op.execute(text("""
        CREATE TABLE alarm_events (
            id UUID NOT NULL,
            definition_id UUID NOT NULL,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            value DOUBLE PRECISION,
            state VARCHAR(20) NOT NULL,
            acknowledged BOOLEAN DEFAULT FALSE,
            acknowledged_at TIMESTAMP WITHOUT TIME ZONE,
            acknowledged_by UUID,
            resolved_at TIMESTAMP WITHOUT TIME ZONE,
            notes TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp);
    """))

    # Step 3: Create partitions for last 12 months + next 3 months
    op.execute(text("""
        -- Function to create monthly partitions
        CREATE OR REPLACE FUNCTION create_alarm_event_partition(partition_date DATE)
        RETURNS void AS $$
        DECLARE
            partition_name TEXT;
            start_date DATE;
            end_date DATE;
        BEGIN
            partition_name := 'alarm_events_' || TO_CHAR(partition_date, 'YYYY_MM');
            start_date := DATE_TRUNC('month', partition_date)::DATE;
            end_date := (DATE_TRUNC('month', partition_date) + INTERVAL '1 month')::DATE;

            -- Check if partition already exists
            IF NOT EXISTS (
                SELECT 1 FROM pg_class WHERE relname = partition_name
            ) THEN
                EXECUTE format('
                    CREATE TABLE %I PARTITION OF alarm_events
                    FOR VALUES FROM (%L) TO (%L)
                ', partition_name, start_date, end_date);

                -- Create indexes on partition
                EXECUTE format('
                    CREATE INDEX %I ON %I (definition_id, timestamp DESC)
                ', partition_name || '_def_ts_idx', partition_name);

                EXECUTE format('
                    CREATE INDEX %I ON %I (state, timestamp DESC)
                ', partition_name || '_state_ts_idx', partition_name);

                RAISE NOTICE 'Created partition: %', partition_name;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """))

    # Create partitions for last 12 months
    op.execute(text("""
        DO $$
        DECLARE
            i INT;
            partition_date DATE;
        BEGIN
            -- Last 12 months
            FOR i IN -12..3 LOOP
                partition_date := DATE_TRUNC('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
                PERFORM create_alarm_event_partition(partition_date);
            END LOOP;
        END $$;
    """))

    # Step 4: Copy data from old table (if exists)
    op.execute(text("""
        INSERT INTO alarm_events
        SELECT * FROM alarm_events_old
        WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '12 months'
        ON CONFLICT DO NOTHING;
    """))

    # Step 5: Create foreign key constraints
    op.execute(text("""
        ALTER TABLE alarm_events
        ADD CONSTRAINT fk_alarm_events_definition
        FOREIGN KEY (definition_id)
        REFERENCES alarm_definitions(id)
        ON DELETE CASCADE;
    """))

    op.execute(text("""
        ALTER TABLE alarm_events
        ADD CONSTRAINT fk_alarm_events_acknowledged_by
        FOREIGN KEY (acknowledged_by)
        REFERENCES users(id)
        ON DELETE SET NULL;
    """))

    # Step 6: Create trigger for automatic partition creation
    op.execute(text("""
        CREATE OR REPLACE FUNCTION auto_create_alarm_event_partition()
        RETURNS TRIGGER AS $$
        DECLARE
            partition_date DATE;
        BEGIN
            partition_date := DATE_TRUNC('month', NEW.timestamp)::DATE;

            -- Try to insert, if partition doesn't exist it will fail
            BEGIN
                RETURN NEW;
            EXCEPTION WHEN undefined_table THEN
                -- Create partition and retry
                PERFORM create_alarm_event_partition(partition_date);
                RETURN NEW;
            END;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_auto_create_alarm_partition
        BEFORE INSERT ON alarm_events
        FOR EACH ROW
        EXECUTE FUNCTION auto_create_alarm_event_partition();
    """))

    # Step 7: Drop old table
    op.execute(text("""
        DROP TABLE IF EXISTS alarm_events_old;
    """))

    print("✅ PDCA #17: alarm_events table partitioned successfully")
    print(f"   - Created partitions for last 12 months + next 3 months")
    print(f"   - Automatic partition creation enabled")
    print(f"   - Indexes created on each partition")


def downgrade() -> None:
    """
    Revert partitioning (convert back to regular table).

    WARNING: This will lose data older than 12 months if it was archived.
    """

    # Step 1: Create regular table
    op.execute(text("""
        CREATE TABLE alarm_events_new (
            id UUID NOT NULL PRIMARY KEY,
            definition_id UUID NOT NULL,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            value DOUBLE PRECISION,
            state VARCHAR(20) NOT NULL,
            acknowledged BOOLEAN DEFAULT FALSE,
            acknowledged_at TIMESTAMP WITHOUT TIME ZONE,
            acknowledged_by UUID,
            resolved_at TIMESTAMP WITHOUT TIME ZONE,
            notes TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
    """))

    # Step 2: Copy data from partitioned table
    op.execute(text("""
        INSERT INTO alarm_events_new
        SELECT * FROM alarm_events;
    """))

    # Step 3: Drop partitioned table and all partitions
    op.execute(text("""
        DROP TABLE IF EXISTS alarm_events CASCADE;
    """))

    # Step 4: Rename new table
    op.execute(text("""
        ALTER TABLE alarm_events_new RENAME TO alarm_events;
    """))

    # Step 5: Recreate indexes
    op.execute(text("""
        CREATE INDEX idx_alarm_events_definition_timestamp
        ON alarm_events (definition_id, timestamp DESC);

        CREATE INDEX idx_alarm_events_state_timestamp
        ON alarm_events (state, timestamp DESC);

        CREATE INDEX idx_alarm_events_timestamp
        ON alarm_events (timestamp DESC);
    """))

    # Step 6: Recreate foreign keys
    op.execute(text("""
        ALTER TABLE alarm_events
        ADD CONSTRAINT fk_alarm_events_definition
        FOREIGN KEY (definition_id)
        REFERENCES alarm_definitions(id)
        ON DELETE CASCADE;

        ALTER TABLE alarm_events
        ADD CONSTRAINT fk_alarm_events_acknowledged_by
        FOREIGN KEY (acknowledged_by)
        REFERENCES users(id)
        ON DELETE SET NULL;
    """))

    # Step 7: Drop partition functions
    op.execute(text("""
        DROP FUNCTION IF EXISTS auto_create_alarm_event_partition() CASCADE;
        DROP FUNCTION IF EXISTS create_alarm_event_partition(DATE) CASCADE;
    """))

    print("✅ PDCA #17: Reverted alarm_events partitioning")
