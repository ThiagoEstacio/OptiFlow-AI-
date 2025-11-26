--
-- PostgreSQL database dump
--

\restrict mmfxgPDBtU0JgMfiVyco5H90rSKzGkTJMmekMDdHpWWmkjA9Puw5828N3jfObfR

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: optiflow
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO optiflow;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: optiflow
--

COMMENT ON SCHEMA public IS '';


--
-- Name: alarmseverity; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.alarmseverity AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);


ALTER TYPE public.alarmseverity OWNER TO optiflow;

--
-- Name: alarmstate; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.alarmstate AS ENUM (
    'ACTIVE',
    'ACKNOWLEDGED',
    'CLEARED'
);


ALTER TYPE public.alarmstate OWNER TO optiflow;

--
-- Name: alarmtype; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.alarmtype AS ENUM (
    'HIGH_LIMIT',
    'LOW_LIMIT',
    'RATE_OF_CHANGE',
    'DEVIATION',
    'PREDICTIVE',
    'CUSTOM'
);


ALTER TYPE public.alarmtype OWNER TO optiflow;

--
-- Name: asset_attribute_type; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.asset_attribute_type AS ENUM (
    'tag_reference',
    'static',
    'calculated'
);


ALTER TYPE public.asset_attribute_type OWNER TO optiflow;

--
-- Name: assettype; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.assettype AS ENUM (
    'ENTERPRISE',
    'SITE',
    'AREA',
    'UNIT',
    'EQUIPMENT',
    'COMPONENT'
);


ALTER TYPE public.assettype OWNER TO optiflow;

--
-- Name: dashboardmodule; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.dashboardmodule AS ENUM (
    'OPERATIONS',
    'MAINTENANCE',
    'ENGINEERING',
    'EXECUTIVE'
);


ALTER TYPE public.dashboardmodule OWNER TO optiflow;

--
-- Name: deviceprotocol; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.deviceprotocol AS ENUM (
    'OPC_UA',
    'MODBUS_TCP',
    'MODBUS_RTU',
    'MQTT',
    'S7',
    'ETHERNET_IP',
    'HTTP'
);


ALTER TYPE public.deviceprotocol OWNER TO optiflow;

--
-- Name: devicestatus; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.devicestatus AS ENUM (
    'CONNECTED',
    'DISCONNECTED',
    'ERROR',
    'UNKNOWN'
);


ALTER TYPE public.devicestatus OWNER TO optiflow;

--
-- Name: gatewaytype; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.gatewaytype AS ENUM (
    'OPCUA',
    'MODBUS_TCP',
    'SIEMENS_S7',
    'ROCKWELL_EIP'
);


ALTER TYPE public.gatewaytype OWNER TO optiflow;

--
-- Name: healthalertseverity; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.healthalertseverity AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);


ALTER TYPE public.healthalertseverity OWNER TO optiflow;

--
-- Name: healthalertstate; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.healthalertstate AS ENUM (
    'ACTIVE',
    'ACKNOWLEDGED',
    'RESOLVED'
);


ALTER TYPE public.healthalertstate OWNER TO optiflow;

--
-- Name: messagerole; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.messagerole AS ENUM (
    'USER',
    'ASSISTANT',
    'SYSTEM'
);


ALTER TYPE public.messagerole OWNER TO optiflow;

--
-- Name: modelstatus; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.modelstatus AS ENUM (
    'TRAINING',
    'ACTIVE',
    'INACTIVE',
    'FAILED'
);


ALTER TYPE public.modelstatus OWNER TO optiflow;

--
-- Name: modeltype; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.modeltype AS ENUM (
    'PREDICTIVE_MAINTENANCE',
    'ANOMALY_DETECTION',
    'DEMAND_FORECAST',
    'PROCESS_OPTIMIZATION',
    'CLASSIFICATION',
    'REGRESSION'
);


ALTER TYPE public.modeltype OWNER TO optiflow;

--
-- Name: tagcategory; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.tagcategory AS ENUM (
    'PROCESS',
    'ENERGY',
    'QUALITY',
    'PRODUCTION',
    'MAINTENANCE',
    'ALARM',
    'SETPOINT',
    'STATUS'
);


ALTER TYPE public.tagcategory OWNER TO optiflow;

--
-- Name: tagdatatype; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.tagdatatype AS ENUM (
    'BOOLEAN',
    'INTEGER',
    'FLOAT',
    'STRING',
    'DOUBLE'
);


ALTER TYPE public.tagdatatype OWNER TO optiflow;

--
-- Name: tagtype; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.tagtype AS ENUM (
    'PHYSICAL',
    'CALCULATED',
    'LOGICAL',
    'AGGREGATED'
);


ALTER TYPE public.tagtype OWNER TO optiflow;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'ENGINEER',
    'OPERATOR',
    'VIEWER'
);


ALTER TYPE public.userrole OWNER TO optiflow;

--
-- Name: widgettype; Type: TYPE; Schema: public; Owner: optiflow
--

CREATE TYPE public.widgettype AS ENUM (
    'KPI_CARD',
    'LINE_CHART',
    'BAR_CHART',
    'PIE_CHART',
    'TABLE',
    'GAUGE',
    'MAP',
    'HEATMAP',
    'PROCESS_STATUS',
    'ACTIVE_ALARMS',
    'PROCESS_VARIABLES',
    'RECENT_COMMANDS',
    'OPERATIONAL_EFFICIENCY',
    'EQUIPMENT_STATUS',
    'EVENT_LOG',
    'OPEN_WORK_ORDERS',
    'MTBF_MTTR',
    'UPCOMING_MAINTENANCE',
    'FAILURE_HISTORY',
    'PREDICTIVE_INDICATORS',
    'PARTS_INVENTORY',
    'MAINTENANCE_RESPONSE_TIME',
    'OPTIMIZATION_RECOMMENDATIONS',
    'PERFORMANCE_ANALYSIS',
    'ENERGY_CONSUMPTION',
    'TREND_ANALYSIS',
    'PROCESS_SIMULATIONS',
    'QUALITY_INDICATORS',
    'CAPACITY_ANALYSIS',
    'KPI_DASHBOARD',
    'SYSTEM_HEALTH',
    'FINANCIAL_ANALYSIS',
    'RISKS_OPPORTUNITIES',
    'MONTHLY_TRENDS',
    'PERFORMANCE_COMPARISON',
    'SUSTAINABILITY_INDICATORS'
);


ALTER TYPE public.widgettype OWNER TO optiflow;

--
-- Name: refresh_alarm_statistics_view(); Type: FUNCTION; Schema: public; Owner: optiflow
--

CREATE FUNCTION public.refresh_alarm_statistics_view() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_alarm_statistics;
END;
$$;


ALTER FUNCTION public.refresh_alarm_statistics_view() OWNER TO optiflow;

--
-- Name: refresh_all_materialized_views(); Type: FUNCTION; Schema: public; Owner: optiflow
--

CREATE FUNCTION public.refresh_all_materialized_views() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_operations_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_asset_health_overview;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_alarm_statistics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tag_performance_metrics;
    
    RAISE NOTICE 'All materialized views refreshed at %', NOW();
END;
$$;


ALTER FUNCTION public.refresh_all_materialized_views() OWNER TO optiflow;

--
-- Name: FUNCTION refresh_all_materialized_views(); Type: COMMENT; Schema: public; Owner: optiflow
--

COMMENT ON FUNCTION public.refresh_all_materialized_views() IS 'Refreshes all materialized views. Should be called by scheduler every 15-30 minutes.';


--
-- Name: refresh_asset_health_view(); Type: FUNCTION; Schema: public; Owner: optiflow
--

CREATE FUNCTION public.refresh_asset_health_view() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_asset_health_overview;
END;
$$;


ALTER FUNCTION public.refresh_asset_health_view() OWNER TO optiflow;

--
-- Name: refresh_daily_operations_view(); Type: FUNCTION; Schema: public; Owner: optiflow
--

CREATE FUNCTION public.refresh_daily_operations_view() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_operations_summary;
    RAISE NOTICE 'Daily operations view refreshed at %', NOW();
END;
$$;


ALTER FUNCTION public.refresh_daily_operations_view() OWNER TO optiflow;

--
-- Name: FUNCTION refresh_daily_operations_view(); Type: COMMENT; Schema: public; Owner: optiflow
--

COMMENT ON FUNCTION public.refresh_daily_operations_view() IS 'Refreshes daily operations materialized view. Call every hour via scheduler.';


--
-- Name: refresh_tag_performance_view(); Type: FUNCTION; Schema: public; Owner: optiflow
--

CREATE FUNCTION public.refresh_tag_performance_view() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tag_performance;
END;
$$;


ALTER FUNCTION public.refresh_tag_performance_view() OWNER TO optiflow;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: optiflow
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO optiflow;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alarm_definitions; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.alarm_definitions (
    id uuid NOT NULL,
    tag_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    alarm_type public.alarmtype NOT NULL,
    severity public.alarmseverity NOT NULL,
    high_limit double precision,
    low_limit double precision,
    deadband double precision,
    delay_seconds double precision NOT NULL,
    enable_email boolean NOT NULL,
    enable_sms boolean NOT NULL,
    notification_recipients jsonb NOT NULL,
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    high_high_limit double precision,
    low_low_limit double precision,
    setpoint double precision,
    deviation_limit double precision
);


ALTER TABLE public.alarm_definitions OWNER TO optiflow;

--
-- Name: alarm_events; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.alarm_events (
    id uuid NOT NULL,
    definition_id uuid NOT NULL,
    state public.alarmstate NOT NULL,
    trigger_value double precision,
    trigger_timestamp timestamp with time zone NOT NULL,
    acknowledged_at timestamp with time zone,
    acknowledged_by uuid,
    acknowledgment_comment text,
    cleared_at timestamp with time zone,
    clear_value double precision,
    duration_seconds double precision,
    event_metadata jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.alarm_events OWNER TO optiflow;

--
-- Name: asset_attributes; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.asset_attributes (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    attribute_type public.asset_attribute_type NOT NULL,
    tag_id uuid,
    static_value character varying(500),
    formula text,
    unit character varying(50),
    display_order integer NOT NULL,
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.asset_attributes OWNER TO optiflow;

--
-- Name: asset_health_alerts; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.asset_health_alerts (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    severity public.healthalertseverity NOT NULL,
    state public.healthalertstate NOT NULL,
    health_score double precision NOT NULL,
    health_status character varying(50) NOT NULL,
    issues_count double precision NOT NULL,
    warnings_count double precision NOT NULL,
    problematic_attributes jsonb NOT NULL,
    recommendations jsonb NOT NULL,
    alert_metadata jsonb NOT NULL,
    acknowledged_at timestamp with time zone,
    acknowledged_by uuid,
    acknowledgment_comment text,
    resolved_at timestamp with time zone,
    resolved_by uuid,
    resolution_comment text,
    resolved_health_score double precision,
    notification_sent boolean NOT NULL,
    notification_sent_at timestamp with time zone,
    auto_resolved boolean NOT NULL,
    triggered_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.asset_health_alerts OWNER TO optiflow;

--
-- Name: asset_health_history; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.asset_health_history (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    snapshot_time timestamp with time zone NOT NULL,
    health_score double precision NOT NULL,
    health_status character varying(50) NOT NULL,
    issues_count integer NOT NULL,
    warnings_count integer NOT NULL,
    attributes_evaluated integer NOT NULL,
    attribute_scores jsonb NOT NULL,
    issues_snapshot jsonb NOT NULL,
    warnings_snapshot jsonb NOT NULL,
    asset_metadata jsonb NOT NULL,
    health_score_change double precision,
    trend_direction character varying(20),
    velocity double precision,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.asset_health_history OWNER TO optiflow;

--
-- Name: asset_templates; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.asset_templates (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    asset_type public.assettype NOT NULL,
    attribute_definitions jsonb NOT NULL,
    analyses jsonb NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.asset_templates OWNER TO optiflow;

--
-- Name: assets; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.assets (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    asset_type public.assettype NOT NULL,
    parent_id uuid,
    template_id uuid,
    is_active boolean NOT NULL,
    asset_metadata jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    path character varying(1000),
    level integer DEFAULT 0,
    icon character varying(100),
    color character varying(20),
    site_id integer,
    health_score integer,
    last_maintenance timestamp with time zone,
    next_maintenance timestamp with time zone,
    status character varying(50) DEFAULT 'operational'::character varying
);


ALTER TABLE public.assets OWNER TO optiflow;

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.conversations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    context json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.conversations OWNER TO optiflow;

--
-- Name: COLUMN conversations.context; Type: COMMENT; Schema: public; Owner: optiflow
--

COMMENT ON COLUMN public.conversations.context IS 'Contextual information for the conversation';


--
-- Name: daily_operations; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.daily_operations (
    id integer NOT NULL,
    operation_date date NOT NULL,
    trucks_received integer,
    trucks_total_tonnage double precision,
    trucks_avg_wait_time double precision,
    ships_in_port integer,
    ships_loading integer,
    ships_departed integer,
    ships_total_tonnage double precision,
    total_tonnage_loaded double precision,
    avg_loading_rate double precision,
    operating_hours double precision,
    downtime_hours double precision,
    shiploaders_available integer,
    shiploaders_operating integer,
    conveyors_available integer,
    conveyors_operating integer,
    corn_tonnage double precision,
    soy_tonnage double precision,
    wheat_tonnage double precision,
    other_tonnage double precision,
    weather_condition character varying(100),
    avg_temperature double precision,
    rainfall_mm double precision,
    wind_speed_kmh double precision,
    weather_delays_hours double precision,
    incidents_count integer,
    incidents_description text,
    maintenance_hours double precision,
    operational_efficiency double precision,
    equipment_utilization double precision,
    notes text,
    site_id uuid NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.daily_operations OWNER TO optiflow;

--
-- Name: daily_operations_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.daily_operations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.daily_operations_id_seq OWNER TO optiflow;

--
-- Name: daily_operations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.daily_operations_id_seq OWNED BY public.daily_operations.id;


--
-- Name: dashboard_shares; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.dashboard_shares (
    id uuid NOT NULL,
    dashboard_id uuid NOT NULL,
    user_id uuid NOT NULL,
    can_edit boolean NOT NULL,
    can_delete boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    shared_by uuid
);


ALTER TABLE public.dashboard_shares OWNER TO optiflow;

--
-- Name: dashboard_templates; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.dashboard_templates (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    module public.dashboardmodule NOT NULL,
    config jsonb NOT NULL,
    thumbnail_url character varying(500),
    is_active boolean NOT NULL,
    is_system boolean NOT NULL,
    usage_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.dashboard_templates OWNER TO optiflow;

--
-- Name: dashboards; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.dashboards (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    module public.dashboardmodule NOT NULL,
    is_public boolean NOT NULL,
    is_template boolean NOT NULL,
    layout_config jsonb NOT NULL,
    default_filters jsonb NOT NULL,
    refresh_interval integer NOT NULL,
    auto_refresh boolean NOT NULL,
    theme character varying(50) NOT NULL,
    show_legend boolean NOT NULL,
    show_grid boolean NOT NULL,
    view_count integer NOT NULL,
    last_viewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.dashboards OWNER TO optiflow;

--
-- Name: data_imports; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.data_imports (
    id integer NOT NULL,
    data_source_id integer NOT NULL,
    import_type character varying(50) NOT NULL,
    file_name character varying(500),
    file_size_bytes integer,
    status character varying(50),
    records_total integer,
    records_imported integer,
    records_failed integer,
    records_duplicate integer,
    errors json,
    warnings json,
    requires_approval boolean,
    approved_by uuid,
    approved_at timestamp with time zone,
    approval_notes text,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    processing_duration_seconds double precision,
    raw_data_sample json,
    site_id uuid NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.data_imports OWNER TO optiflow;

--
-- Name: data_imports_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.data_imports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_imports_id_seq OWNER TO optiflow;

--
-- Name: data_imports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.data_imports_id_seq OWNED BY public.data_imports.id;


--
-- Name: data_sources; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.data_sources (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    source_type character varying(50) NOT NULL,
    api_url character varying(500),
    api_key_encrypted text,
    auth_type character varying(50),
    data_format character varying(50),
    field_mapping json,
    auto_sync boolean,
    sync_interval_minutes integer,
    last_sync_at timestamp with time zone,
    last_sync_status character varying(50),
    last_sync_error text,
    validation_rules json,
    require_approval boolean,
    enabled boolean,
    notes text,
    site_id uuid NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.data_sources OWNER TO optiflow;

--
-- Name: data_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.data_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_sources_id_seq OWNER TO optiflow;

--
-- Name: data_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.data_sources_id_seq OWNED BY public.data_sources.id;


--
-- Name: devices; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.devices (
    id uuid NOT NULL,
    site_id uuid,
    name character varying(255) NOT NULL,
    description text,
    protocol public.deviceprotocol NOT NULL,
    is_active boolean NOT NULL,
    connection_config jsonb NOT NULL,
    status public.devicestatus NOT NULL,
    last_seen timestamp with time zone,
    error_message text,
    manufacturer character varying(100),
    model character varying(100),
    serial_number character varying(100),
    firmware_version character varying(50),
    total_tags integer NOT NULL,
    data_points_collected integer NOT NULL,
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.devices OWNER TO optiflow;

--
-- Name: gateway_configs; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.gateway_configs (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    gateway_type public.gatewaytype NOT NULL,
    enabled boolean NOT NULL,
    connection_config json NOT NULL,
    polling_interval_ms integer NOT NULL,
    max_retries integer NOT NULL,
    base_retry_delay integer NOT NULL,
    max_buffer_size integer NOT NULL,
    description character varying(500),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.gateway_configs OWNER TO optiflow;

--
-- Name: gateway_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.gateway_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gateway_configs_id_seq OWNER TO optiflow;

--
-- Name: gateway_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.gateway_configs_id_seq OWNED BY public.gateway_configs.id;


--
-- Name: gateway_health_logs; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.gateway_health_logs (
    id integer NOT NULL,
    gateway_name character varying(200) NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(50) NOT NULL,
    successful_reads integer,
    failed_reads integer,
    buffer_size integer,
    uptime_seconds double precision,
    last_error character varying(1000)
);


ALTER TABLE public.gateway_health_logs OWNER TO optiflow;

--
-- Name: gateway_health_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.gateway_health_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gateway_health_logs_id_seq OWNER TO optiflow;

--
-- Name: gateway_health_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.gateway_health_logs_id_seq OWNED BY public.gateway_health_logs.id;


--
-- Name: gateway_tags; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.gateway_tags (
    id integer NOT NULL,
    gateway_id integer NOT NULL,
    tag_name character varying(200) NOT NULL,
    enabled boolean NOT NULL,
    address_config json NOT NULL,
    data_type character varying(50),
    scale_factor double precision,
    "offset" double precision,
    unit character varying(50),
    description character varying(500),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.gateway_tags OWNER TO optiflow;

--
-- Name: gateway_tags_extended; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.gateway_tags_extended (
    id integer NOT NULL,
    gateway_id integer,
    tag_name character varying(200) NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    asset_id uuid,
    tag_group character varying(200),
    tag_type character varying(50) DEFAULT 'physical'::character varying NOT NULL,
    address_config jsonb,
    data_type character varying(50) DEFAULT 'float'::character varying,
    scale_factor double precision DEFAULT 1.0,
    tag_offset double precision DEFAULT 0.0,
    formula text,
    formula_tags jsonb,
    condition text,
    unit character varying(50),
    min_value double precision,
    max_value double precision,
    archive_enabled boolean DEFAULT true,
    archive_type character varying(50) DEFAULT 'on_change'::character varying,
    archive_deadband double precision,
    archive_interval_seconds integer,
    compression_deviation double precision,
    quality_enabled boolean DEFAULT true,
    alarm_enabled boolean DEFAULT false,
    alarm_config jsonb,
    description character varying(1000),
    category character varying(100),
    properties jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    CONSTRAINT gateway_tags_extended_tag_type_check CHECK (((tag_type)::text = ANY ((ARRAY['physical'::character varying, 'calculated'::character varying, 'logical'::character varying, 'aggregated'::character varying])::text[])))
);


ALTER TABLE public.gateway_tags_extended OWNER TO optiflow;

--
-- Name: gateway_tags_extended_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.gateway_tags_extended_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gateway_tags_extended_id_seq OWNER TO optiflow;

--
-- Name: gateway_tags_extended_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.gateway_tags_extended_id_seq OWNED BY public.gateway_tags_extended.id;


--
-- Name: gateway_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.gateway_tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gateway_tags_id_seq OWNER TO optiflow;

--
-- Name: gateway_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.gateway_tags_id_seq OWNED BY public.gateway_tags.id;


--
-- Name: gbm_logistics_data; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.gbm_logistics_data (
    id integer NOT NULL,
    import_id integer,
    operation_type character varying(50) NOT NULL,
    external_id character varying(200),
    external_reference character varying(200),
    operation_date timestamp with time zone NOT NULL,
    completion_date timestamp with time zone,
    vehicle_id character varying(100),
    vehicle_type character varying(50),
    product_type character varying(100),
    product_grade character varying(50),
    gross_weight_kg double precision,
    tare_weight_kg double precision,
    net_weight_kg double precision NOT NULL,
    moisture_percent double precision,
    impurity_percent double precision,
    protein_percent double precision,
    broken_percent double precision,
    quality_approved boolean,
    quality_notes text,
    origin character varying(200),
    origin_city character varying(100),
    origin_state character varying(50),
    destination character varying(200),
    destination_country character varying(100),
    loading_time_minutes double precision,
    waiting_time_minutes double precision,
    total_time_minutes double precision,
    throughput_kg_per_hour double precision,
    freight_value double precision,
    storage_value double precision,
    service_value double precision,
    total_value double precision,
    status character varying(50),
    berth_number integer,
    shiploader_id character varying(50),
    conveyor_ids json,
    contract_number character varying(100),
    buyer_company character varying(200),
    supplier_company character varying(200),
    weather_condition character varying(100),
    incidents text,
    delays_description text,
    notes text,
    raw_data json,
    validated boolean,
    validated_by uuid,
    validated_at timestamp with time zone,
    validation_notes text,
    site_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.gbm_logistics_data OWNER TO optiflow;

--
-- Name: gbm_logistics_data_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.gbm_logistics_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gbm_logistics_data_id_seq OWNER TO optiflow;

--
-- Name: gbm_logistics_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.gbm_logistics_data_id_seq OWNED BY public.gbm_logistics_data.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.messages (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    role public.messagerole NOT NULL,
    content text NOT NULL,
    message_metadata json,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.messages OWNER TO optiflow;

--
-- Name: COLUMN messages.message_metadata; Type: COMMENT; Schema: public; Owner: optiflow
--

COMMENT ON COLUMN public.messages.message_metadata IS 'Additional metadata like tokens, model used, etc.';


--
-- Name: ml_models; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.ml_models (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    model_type public.modeltype NOT NULL,
    status public.modelstatus NOT NULL,
    mlflow_run_id character varying(255),
    mlflow_model_uri character varying(500),
    version character varying(50) NOT NULL,
    algorithm character varying(100) NOT NULL,
    metrics jsonb NOT NULL,
    training_start timestamp with time zone,
    training_end timestamp with time zone,
    training_samples integer,
    feature_names jsonb NOT NULL,
    feature_importance jsonb NOT NULL,
    hyperparameters jsonb NOT NULL,
    deployed_at timestamp with time zone,
    is_active boolean NOT NULL,
    retrain_frequency_days integer,
    last_retrain timestamp with time zone,
    next_retrain timestamp with time zone,
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ml_models OWNER TO optiflow;

--
-- Name: tags; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.tags (
    id uuid NOT NULL,
    device_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    address character varying(500) NOT NULL,
    data_type public.tagdatatype NOT NULL,
    unit character varying(50),
    category public.tagcategory NOT NULL,
    min_value double precision,
    max_value double precision,
    engineering_min double precision,
    engineering_max double precision,
    scale double precision NOT NULL,
    "offset" double precision NOT NULL,
    scan_rate_ms integer NOT NULL,
    deadband double precision,
    enable_quality_check boolean NOT NULL,
    last_value character varying(100),
    last_quality character varying(20),
    last_timestamp timestamp with time zone,
    data_points_count integer NOT NULL,
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tags OWNER TO optiflow;

--
-- Name: mv_alarm_statistics; Type: MATERIALIZED VIEW; Schema: public; Owner: optiflow
--

CREATE MATERIALIZED VIEW public.mv_alarm_statistics AS
 SELECT date_trunc('day'::text, ae.trigger_timestamp) AS alarm_date,
    ad.tag_id,
    t.name AS tag_name,
    t.device_id,
    d.name AS device_name,
    count(*) AS total_alarms,
    count(*) FILTER (WHERE (ad.severity = 'CRITICAL'::public.alarmseverity)) AS critical_alarms,
    count(*) FILTER (WHERE (ad.severity = 'HIGH'::public.alarmseverity)) AS high_alarms,
    count(*) FILTER (WHERE (ad.severity = 'MEDIUM'::public.alarmseverity)) AS medium_alarms,
    count(*) FILTER (WHERE (ad.severity = 'LOW'::public.alarmseverity)) AS low_alarms,
    count(*) FILTER (WHERE (ae.state = 'ACTIVE'::public.alarmstate)) AS active_alarms,
    count(*) FILTER (WHERE (ae.state = 'ACKNOWLEDGED'::public.alarmstate)) AS acknowledged_alarms,
    count(*) FILTER (WHERE (ae.state = 'CLEARED'::public.alarmstate)) AS cleared_alarms,
    avg(ae.duration_seconds) AS avg_duration_seconds,
    max(ae.duration_seconds) AS max_duration_seconds,
    min(ae.duration_seconds) AS min_duration_seconds,
    avg(EXTRACT(epoch FROM (ae.acknowledged_at - ae.trigger_timestamp))) FILTER (WHERE (ae.acknowledged_at IS NOT NULL)) AS avg_acknowledge_time_seconds,
    avg(EXTRACT(epoch FROM (ae.cleared_at - ae.trigger_timestamp))) FILTER (WHERE (ae.cleared_at IS NOT NULL)) AS avg_clear_time_seconds,
    CURRENT_TIMESTAMP AS view_refreshed_at
   FROM (((public.alarm_events ae
     JOIN public.alarm_definitions ad ON ((ae.definition_id = ad.id)))
     JOIN public.tags t ON ((ad.tag_id = t.id)))
     JOIN public.devices d ON ((t.device_id = d.id)))
  WHERE (ae.trigger_timestamp IS NOT NULL)
  GROUP BY (date_trunc('day'::text, ae.trigger_timestamp)), ad.tag_id, t.name, t.device_id, d.name
  WITH NO DATA;


ALTER TABLE public.mv_alarm_statistics OWNER TO optiflow;

--
-- Name: MATERIALIZED VIEW mv_alarm_statistics; Type: COMMENT; Schema: public; Owner: optiflow
--

COMMENT ON MATERIALIZED VIEW public.mv_alarm_statistics IS 'Daily alarm aggregations by tag/device. Refresh every 1 hour. Expected: -70% query time on alarm trends.';


--
-- Name: mv_asset_health_overview; Type: MATERIALIZED VIEW; Schema: public; Owner: optiflow
--

CREATE MATERIALIZED VIEW public.mv_asset_health_overview AS
 SELECT a.id AS asset_id,
    a.name AS asset_name,
    a.asset_type,
    a.site_id,
    a.status,
        CASE
            WHEN ((a.status)::text = 'OPERATIONAL'::text) THEN 95.0
            WHEN ((a.status)::text = 'WARNING'::text) THEN 75.0
            WHEN ((a.status)::text = 'ALARM'::text) THEN 50.0
            WHEN ((a.status)::text = 'MAINTENANCE'::text) THEN 30.0
            ELSE 0.0
        END AS health_score,
    count(DISTINCT aa.id) AS total_attributes,
    a.last_maintenance,
    a.updated_at AS last_updated,
    CURRENT_TIMESTAMP AS view_refreshed_at
   FROM (public.assets a
     LEFT JOIN public.asset_attributes aa ON ((a.id = aa.asset_id)))
  GROUP BY a.id, a.name, a.asset_type, a.site_id, a.status, a.last_maintenance, a.updated_at
  WITH NO DATA;


ALTER TABLE public.mv_asset_health_overview OWNER TO optiflow;

--
-- Name: truck_entries; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.truck_entries (
    id integer NOT NULL,
    truck_id character varying(50) NOT NULL,
    driver_name character varying(200),
    company character varying(200),
    gross_weight double precision NOT NULL,
    tare_weight double precision NOT NULL,
    net_weight double precision NOT NULL,
    product_type character varying(100) NOT NULL,
    product_quality character varying(50),
    moisture_percent double precision,
    impurity_percent double precision,
    origin_farm character varying(200),
    origin_city character varying(200),
    origin_state character varying(50),
    entry_time timestamp with time zone NOT NULL,
    gross_weight_time timestamp with time zone,
    tare_weight_time timestamp with time zone,
    exit_time timestamp with time zone,
    status character varying(50),
    notes text,
    site_id uuid NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.truck_entries OWNER TO optiflow;

--
-- Name: mv_daily_operations_summary; Type: MATERIALIZED VIEW; Schema: public; Owner: optiflow
--

CREATE MATERIALIZED VIEW public.mv_daily_operations_summary AS
 SELECT date_trunc('day'::text, truck_entries.entry_time) AS operation_date,
    truck_entries.site_id,
    count(*) AS total_trucks,
    count(DISTINCT truck_entries.truck_id) AS unique_trucks,
    sum((truck_entries.gross_weight - truck_entries.tare_weight)) AS total_net_weight,
    avg((truck_entries.gross_weight - truck_entries.tare_weight)) AS avg_net_weight,
    count(*) FILTER (WHERE ((truck_entries.product_type)::text = 'corn'::text)) AS corn_count,
    count(*) FILTER (WHERE ((truck_entries.product_type)::text = 'soy'::text)) AS soy_count,
    count(*) FILTER (WHERE ((truck_entries.product_type)::text = 'wheat'::text)) AS wheat_count,
    avg(truck_entries.moisture_percent) AS avg_moisture,
    avg(truck_entries.impurity_percent) AS avg_impurity,
    min(truck_entries.entry_time) AS first_entry,
    max(truck_entries.entry_time) AS last_entry,
    count(*) FILTER (WHERE ((truck_entries.status)::text = 'completed'::text)) AS completed_count,
    count(*) FILTER (WHERE ((truck_entries.status)::text = 'pending'::text)) AS pending_count,
    count(DISTINCT truck_entries.origin_city) AS unique_origin_cities,
    count(DISTINCT truck_entries.company) AS unique_companies
   FROM public.truck_entries
  WHERE (truck_entries.entry_time >= (now() - '2 years'::interval))
  GROUP BY (date_trunc('day'::text, truck_entries.entry_time)), truck_entries.site_id
  WITH NO DATA;


ALTER TABLE public.mv_daily_operations_summary OWNER TO optiflow;

--
-- Name: MATERIALIZED VIEW mv_daily_operations_summary; Type: COMMENT; Schema: public; Owner: optiflow
--

COMMENT ON MATERIALIZED VIEW public.mv_daily_operations_summary IS 'Daily aggregated operational metrics for truck entries. Refreshed every 1 hour. Reduces query time by -60%.';


--
-- Name: mv_tag_performance; Type: MATERIALIZED VIEW; Schema: public; Owner: optiflow
--

CREATE MATERIALIZED VIEW public.mv_tag_performance AS
 SELECT t.id AS tag_id,
    t.name AS tag_name,
    t.device_id,
    d.name AS device_name,
    t.category,
    t.data_type,
    t.is_active,
    t.data_points_count,
    t.scan_rate_ms,
        CASE
            WHEN (t.last_quality IS NULL) THEN 'NEVER_READ'::text
            WHEN ((t.last_quality)::text = 'GOOD'::text) THEN 'GOOD'::text
            WHEN ((t.last_quality)::text = 'BAD'::text) THEN 'BAD'::text
            ELSE 'UNCERTAIN'::text
        END AS quality_status,
    t.last_timestamp,
        CASE
            WHEN (t.last_timestamp IS NULL) THEN NULL::text
            WHEN (t.last_timestamp < (CURRENT_TIMESTAMP - '01:00:00'::interval)) THEN 'STALE'::text
            WHEN (t.last_timestamp < (CURRENT_TIMESTAMP - '00:10:00'::interval)) THEN 'WARNING'::text
            ELSE 'FRESH'::text
        END AS data_freshness,
    (EXTRACT(epoch FROM (CURRENT_TIMESTAMP - t.last_timestamp)) / (60)::numeric) AS minutes_since_last_update,
    t.min_value,
    t.max_value,
    t.engineering_min,
    t.engineering_max,
    t.unit,
    t.created_at,
    t.updated_at,
    CURRENT_TIMESTAMP AS view_refreshed_at
   FROM (public.tags t
     JOIN public.devices d ON ((t.device_id = d.id)))
  WITH NO DATA;


ALTER TABLE public.mv_tag_performance OWNER TO optiflow;

--
-- Name: MATERIALIZED VIEW mv_tag_performance; Type: COMMENT; Schema: public; Owner: optiflow
--

COMMENT ON MATERIALIZED VIEW public.mv_tag_performance IS 'Tag quality and performance metrics. Refresh every 2 minutes. Expected: -65% query time on tag health dashboards.';


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.organizations (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    contact_name character varying(255),
    contact_email character varying(255),
    contact_phone character varying(50),
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.organizations OWNER TO optiflow;

--
-- Name: predictions; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.predictions (
    id uuid NOT NULL,
    model_id uuid NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id uuid NOT NULL,
    prediction_value double precision,
    prediction_class character varying(100),
    confidence double precision,
    probabilities jsonb NOT NULL,
    features jsonb NOT NULL,
    shap_values jsonb NOT NULL,
    prediction_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    prediction_horizon character varying(50),
    actual_value double precision,
    actual_class character varying(100),
    outcome_timestamp timestamp with time zone,
    prediction_metadata jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.predictions OWNER TO optiflow;

--
-- Name: ship_loadings; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.ship_loadings (
    id integer NOT NULL,
    ship_name character varying(200) NOT NULL,
    ship_imo character varying(20),
    ship_flag character varying(50),
    ship_dwt double precision,
    berth_number integer NOT NULL,
    product_type character varying(100) NOT NULL,
    target_tonnage double precision NOT NULL,
    loaded_tonnage double precision,
    loading_rate_avg double precision,
    loading_rate_peak double precision,
    downtime_hours double precision,
    arrival_time timestamp with time zone,
    berthing_time timestamp with time zone,
    loading_start_time timestamp with time zone,
    loading_end_time timestamp with time zone,
    departure_time timestamp with time zone,
    status character varying(50),
    buyer_company character varying(200),
    destination_port character varying(200),
    destination_country character varying(100),
    contract_number character varying(100),
    average_moisture double precision,
    average_impurity double precision,
    quality_approved boolean,
    quality_notes text,
    weather_conditions character varying(200),
    incidents text,
    notes text,
    site_id uuid NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.ship_loadings OWNER TO optiflow;

--
-- Name: ship_loadings_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.ship_loadings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ship_loadings_id_seq OWNER TO optiflow;

--
-- Name: ship_loadings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.ship_loadings_id_seq OWNED BY public.ship_loadings.id;


--
-- Name: sites; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.sites (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    address character varying(500),
    city character varying(100),
    state character varying(100),
    country character varying(100),
    postal_code character varying(20),
    latitude character varying(50),
    longitude character varying(50),
    site_type character varying(50),
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sites OWNER TO optiflow;

--
-- Name: tag_formulas; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.tag_formulas (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description character varying(1000),
    formula_type character varying(50) NOT NULL,
    expression text NOT NULL,
    input_tags jsonb,
    output_unit character varying(50),
    output_type character varying(50),
    execution_interval_seconds integer,
    is_active boolean DEFAULT true,
    category character varying(100),
    tags_metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.tag_formulas OWNER TO optiflow;

--
-- Name: tag_formulas_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.tag_formulas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tag_formulas_id_seq OWNER TO optiflow;

--
-- Name: tag_formulas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.tag_formulas_id_seq OWNED BY public.tag_formulas.id;


--
-- Name: tag_labels; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.tag_labels (
    id uuid NOT NULL,
    tag_id uuid NOT NULL,
    display_name character varying(255) NOT NULL,
    short_name character varying(100),
    equipment_name character varying(255),
    area_name character varying(255),
    system_name character varying(255),
    custom_description text,
    notes text,
    is_visible boolean NOT NULL,
    is_favorite boolean NOT NULL,
    created_by character varying(255),
    updated_by character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tag_labels OWNER TO optiflow;

--
-- Name: truck_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: optiflow
--

CREATE SEQUENCE public.truck_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.truck_entries_id_seq OWNER TO optiflow;

--
-- Name: truck_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optiflow
--

ALTER SEQUENCE public.truck_entries_id_seq OWNED BY public.truck_entries.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    is_superuser boolean NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    phone character varying(50),
    role public.userrole NOT NULL,
    last_login timestamp with time zone,
    failed_login_attempts integer NOT NULL,
    locked_until timestamp with time zone,
    preferences jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO optiflow;

--
-- Name: widgets; Type: TABLE; Schema: public; Owner: optiflow
--

CREATE TABLE public.widgets (
    id uuid NOT NULL,
    dashboard_id uuid NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    type public.widgettype NOT NULL,
    "position" integer NOT NULL,
    grid_position jsonb NOT NULL,
    config jsonb NOT NULL,
    data_config jsonb NOT NULL,
    display_config jsonb NOT NULL,
    refresh_interval integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.widgets OWNER TO optiflow;

--
-- Name: daily_operations id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.daily_operations ALTER COLUMN id SET DEFAULT nextval('public.daily_operations_id_seq'::regclass);


--
-- Name: data_imports id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_imports ALTER COLUMN id SET DEFAULT nextval('public.data_imports_id_seq'::regclass);


--
-- Name: data_sources id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_sources ALTER COLUMN id SET DEFAULT nextval('public.data_sources_id_seq'::regclass);


--
-- Name: gateway_configs id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_configs ALTER COLUMN id SET DEFAULT nextval('public.gateway_configs_id_seq'::regclass);


--
-- Name: gateway_health_logs id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_health_logs ALTER COLUMN id SET DEFAULT nextval('public.gateway_health_logs_id_seq'::regclass);


--
-- Name: gateway_tags id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_tags ALTER COLUMN id SET DEFAULT nextval('public.gateway_tags_id_seq'::regclass);


--
-- Name: gateway_tags_extended id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_tags_extended ALTER COLUMN id SET DEFAULT nextval('public.gateway_tags_extended_id_seq'::regclass);


--
-- Name: gbm_logistics_data id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gbm_logistics_data ALTER COLUMN id SET DEFAULT nextval('public.gbm_logistics_data_id_seq'::regclass);


--
-- Name: ship_loadings id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.ship_loadings ALTER COLUMN id SET DEFAULT nextval('public.ship_loadings_id_seq'::regclass);


--
-- Name: tag_formulas id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.tag_formulas ALTER COLUMN id SET DEFAULT nextval('public.tag_formulas_id_seq'::regclass);


--
-- Name: truck_entries id; Type: DEFAULT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.truck_entries ALTER COLUMN id SET DEFAULT nextval('public.truck_entries_id_seq'::regclass);


--
-- Data for Name: alarm_definitions; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.alarm_definitions (id, tag_id, name, description, is_active, alarm_type, severity, high_limit, low_limit, deadband, delay_seconds, enable_email, enable_sms, notification_recipients, settings, created_at, updated_at, high_high_limit, low_low_limit, setpoint, deviation_limit) FROM stdin;
7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	3481b08a-a357-48fd-af5d-9aa4677b9564	por_carregamento - High Limit	por_carregamento: High alarm - Value 81.42 > 80.00	t	HIGH_LIMIT	HIGH	80	\N	0	0	f	f	[]	{}	2025-11-25 19:40:06.465741+00	2025-11-25 19:40:06.465741+00	\N	\N	\N	\N
968bfc86-180d-454f-8417-09f433813918	722d6b36-0759-4ebe-8728-3654bdc9e5ba	LOAD_PCT_ALARM_TEST - High Limit	LOAD_PCT_ALARM_TEST: High alarm - Value 74.72 > 70.00	t	HIGH_LIMIT	HIGH	70	\N	0	0	f	f	[]	{}	2025-11-25 19:15:02.717619+00	2025-11-25 19:15:02.717619+00	\N	\N	\N	\N
\.


--
-- Data for Name: alarm_events; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.alarm_events (id, definition_id, state, trigger_value, trigger_timestamp, acknowledged_at, acknowledged_by, acknowledgment_comment, cleared_at, clear_value, duration_seconds, event_metadata, created_at, updated_at) FROM stdin;
f8cdcb83-72ae-472b-a700-3a61239c1500	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.54784135530738	2025-11-25 19:23:14.26401+00	\N	\N	\N	2025-11-25 19:23:16.266878+00	67.80009643110284	2.002868	{}	2025-11-25 19:23:14.269103+00	2025-11-25 19:23:16.279556+00
ff6656a8-6759-45a2-8c10-7a5fd3192395	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.6813110907207	2025-11-25 19:59:51.523668+00	\N	\N	\N	2025-11-25 20:00:21.552457+00	60.96135085534776	30.028789	{}	2025-11-25 19:59:51.534648+00	2025-11-25 20:00:21.560217+00
d7befc54-0ed4-4990-8b24-60da53754b72	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.50274085590189	2025-11-25 19:23:18.272897+00	\N	\N	\N	2025-11-25 19:23:40.289771+00	65.37484935456555	22.016874	{}	2025-11-25 19:23:18.284486+00	2025-11-25 19:23:40.29748+00
4990776b-a293-4123-8148-edf3bc5a1b75	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.51296795176634	2025-11-25 19:59:59.534675+00	\N	\N	\N	2025-11-25 20:00:23.55793+00	62.483008892362356	24.023255	{}	2025-11-25 19:59:59.541152+00	2025-11-25 20:00:23.566423+00
be117751-9d57-4435-a952-ea7dc6ad240f	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.38879062099899	2025-11-25 19:27:26.464932+00	\N	\N	\N	2025-11-25 19:27:56.488075+00	59.154473223609614	30.023143	{}	2025-11-25 19:27:26.473999+00	2025-11-25 19:27:56.499081+00
a8749d21-96b0-4caf-aa96-4f1542154f9c	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.55695094600202	2025-11-25 20:58:47.650535+00	\N	\N	\N	2025-11-25 20:59:15.667486+00	62.884427961774364	28.016951	{}	2025-11-25 20:58:47.653826+00	2025-11-25 20:59:15.67069+00
80779185-5748-4ad1-acd4-35b108025f3f	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.139262965598	2025-11-25 19:29:30.562578+00	\N	\N	\N	2025-11-25 19:29:54.580395+00	67.82777901650668	24.017817	{}	2025-11-25 19:29:30.57154+00	2025-11-25 19:29:54.588835+00
fcd9140a-6085-4560-8998-637237c7e815	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.97842117987571	2025-11-25 20:00:57.590439+00	\N	\N	\N	2025-11-25 20:01:29.616873+00	59.58286271375447	32.026434	{}	2025-11-25 20:00:57.597404+00	2025-11-25 20:01:29.628751+00
bd11ed8f-272a-4470-8742-3cd1bcdb439c	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.09925003094855	2025-11-25 19:30:30.602957+00	\N	\N	\N	2025-11-25 19:30:32.60777+00	63.70352041014817	2.004813	{}	2025-11-25 19:30:30.611509+00	2025-11-25 19:30:32.612736+00
72fd1887-bd12-4610-8be6-eab56bd9e29e	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.502673158814	2025-11-25 21:44:47.177866+00	\N	\N	\N	2025-11-25 21:45:19.193352+00	65.42241960110127	32.015486	{}	2025-11-25 21:44:47.180574+00	2025-11-25 21:45:19.196279+00
1d50b4ca-0588-40ad-8fdd-f01ede5be715	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.10686603985334	2025-11-25 19:35:47.680216+00	\N	\N	\N	2025-11-25 19:36:17.704272+00	59.444424822969566	30.024056	{}	2025-11-25 19:35:47.689606+00	2025-11-25 19:36:17.712421+00
90467139-4732-4919-876c-77d0f18d53a7	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.34439300370177	2025-11-25 20:02:25.666292+00	\N	\N	\N	2025-11-25 20:02:27.674005+00	66.91609260656602	2.007713	{}	2025-11-25 20:02:26.65309+00	2025-11-25 20:02:27.680782+00
90ce514d-8123-4d38-bdfc-109816318d8e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	81.42348151603416	2025-11-25 19:40:06.455799+00	\N	\N	\N	2025-11-25 19:40:10.462397+00	77.34661793273283	4.006598	{}	2025-11-25 19:40:06.465741+00	2025-11-25 19:40:10.470329+00
01a9f997-1f5b-4b7d-8c09-f803dd0a36c0	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.1420266006267	2025-11-25 20:59:53.68751+00	\N	\N	\N	2025-11-25 21:00:17.702491+00	64.71054568757815	24.014981	{}	2025-11-25 20:59:53.690877+00	2025-11-25 21:00:18.52906+00
7f07175c-7973-479f-afbe-99b948cb9ec9	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.4878444457629	2025-11-25 19:40:26.483335+00	\N	\N	\N	2025-11-25 19:40:28.486661+00	65.65610338311876	2.003326	{}	2025-11-25 19:40:26.48754+00	2025-11-25 19:40:28.623954+00
ed52400b-5c3b-424c-9135-b92a06571647	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.267123420497	2025-11-25 20:03:01.702787+00	\N	\N	\N	2025-11-25 20:03:35.737117+00	52.947519768196386	34.03433	{}	2025-11-25 20:03:01.712618+00	2025-11-25 20:03:35.749001+00
ebf524b6-1c8b-48ec-bfb6-9bef9698b2a2	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.14448911305564	2025-11-25 19:56:41.358401+00	\N	\N	\N	2025-11-25 19:57:15.385417+00	60.289000354396734	34.027016	{}	2025-11-25 19:56:41.366817+00	2025-11-25 19:57:15.409626+00
67d074de-6b57-4136-bad8-71ff1f2dd945	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.08097724781358	2025-11-25 22:44:29.100422+00	\N	\N	\N	2025-11-25 22:45:05.123125+00	55.224913333262386	36.022703	{}	2025-11-25 22:44:29.103097+00	2025-11-25 22:45:05.125854+00
3b9749f2-bc10-4251-9a06-5fb87c0ef89a	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.92451179862118	2025-11-25 19:58:55.47242+00	\N	\N	\N	2025-11-25 19:59:15.48714+00	67.25589813212375	20.01472	{}	2025-11-25 19:58:55.483876+00	2025-11-25 19:59:15.495601+00
f8a42a03-42ff-4369-b49f-93eb596b6558	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.16857941727096	2025-11-25 21:00:47.719375+00	\N	\N	\N	2025-11-25 21:01:21.737649+00	59.54903698974376	34.018274	{}	2025-11-25 21:00:47.722228+00	2025-11-25 21:01:22.672552+00
e78fd208-3767-43e7-8be0-40ff103ef7f0	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.02558264127018	2025-11-25 20:05:03.827519+00	\N	\N	\N	2025-11-25 20:05:37.857349+00	61.77826102885869	34.02983	{}	2025-11-25 20:05:03.832315+00	2025-11-25 20:05:37.861867+00
e602c5f9-c0cf-449f-9136-8f62d98af500	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.66905172981144	2025-11-25 21:45:49.208918+00	\N	\N	\N	2025-11-25 21:46:23.22875+00	57.35621831606201	34.019832	{}	2025-11-25 21:45:49.211584+00	2025-11-25 21:46:23.261284+00
fa228bf1-1594-459c-b150-6de52d488278	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.6210177427778	2025-11-25 20:07:17.932895+00	\N	\N	\N	2025-11-25 20:07:37.945259+00	65.97014020098737	20.012364	{}	2025-11-25 20:07:17.938051+00	2025-11-25 20:07:37.952263+00
0789d080-b8ef-4a48-b4f4-a93aa0dfd284	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.73825564575267	2025-11-25 21:01:55.755292+00	\N	\N	\N	2025-11-25 21:02:21.768203+00	62.07318847553676	26.012911	{}	2025-11-25 21:01:55.758575+00	2025-11-25 21:02:21.771727+00
3356e665-3a2d-46d6-a2b7-40f657d108a4	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.77793454734737	2025-11-25 20:52:23.437093+00	\N	\N	\N	2025-11-25 20:52:59.457876+00	62.04006793426471	36.020783	{}	2025-11-25 20:52:23.440603+00	2025-11-25 20:52:59.461044+00
19e5f793-5169-4682-8109-0e789adaf1f4	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.80442263100237	2025-11-25 20:54:37.511968+00	\N	\N	\N	2025-11-25 20:54:59.522791+00	67.11267852077067	22.010823	{}	2025-11-25 20:54:37.515289+00	2025-11-25 20:54:59.526038+00
d1b992e6-e6dc-43a9-986f-47fd3c41f47b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.3557821320061	2025-11-25 21:19:38.336884+00	\N	\N	\N	2025-11-25 21:20:14.357678+00	58.88347143368137	36.020794	{}	2025-11-25 21:19:38.340512+00	2025-11-25 21:20:14.360221+00
4bcba4df-0e34-4ee7-ba69-c7ac9ed5f887	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.42113347007313	2025-11-25 20:55:41.548163+00	\N	\N	\N	2025-11-25 20:56:01.558792+00	67.48504333537471	20.010629	{}	2025-11-25 20:55:41.552325+00	2025-11-25 20:56:01.803232+00
5979b324-36be-44b6-a9e5-5be7428989ff	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.39905337575975	2025-11-25 21:46:57.245715+00	\N	\N	\N	2025-11-25 21:47:31.263217+00	55.72669005223963	34.017502	{}	2025-11-25 21:46:57.248673+00	2025-11-25 21:47:31.266602+00
9083682b-456d-4af4-a8c3-6edf56176973	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.81873118936305	2025-11-25 20:56:39.581864+00	\N	\N	\N	2025-11-25 20:57:07.595648+00	65.15280149878858	28.013784	{}	2025-11-25 20:56:39.585014+00	2025-11-25 20:57:07.599248+00
01830e31-8e2d-4db5-aee5-f5854fc63eaf	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.44277941047145	2025-11-25 21:21:50.410106+00	\N	\N	\N	2025-11-25 21:22:12.421129+00	67.53987173155512	22.011023	{}	2025-11-25 21:21:50.413477+00	2025-11-25 21:22:12.423792+00
f31ba9fa-1a1d-4191-8132-40758e36a6a9	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.07158228745274	2025-11-25 22:47:39.199657+00	\N	\N	\N	2025-11-25 22:48:09.213969+00	58.099391389038054	30.014312	{}	2025-11-25 22:47:39.202256+00	2025-11-25 22:48:09.216083+00
a792df74-883a-4f9b-9219-3da7e92f3594	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.16188881079277	2025-11-25 21:22:48.44153+00	\N	\N	\N	2025-11-25 21:23:22.460074+00	61.15168788625815	34.018544	{}	2025-11-25 21:22:48.444155+00	2025-11-25 21:23:22.462636+00
5c96520e-399b-470e-993a-c57b5f9a59d4	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.3260587015482	2025-11-25 21:48:01.27692+00	\N	\N	\N	2025-11-25 21:48:29.293608+00	59.33527041844286	28.016688	{}	2025-11-25 21:48:01.284967+00	2025-11-25 21:48:29.296547+00
79367d94-f586-4cd4-8e14-76294dbc74c0	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.23083698822903	2025-11-25 21:23:54.476992+00	\N	\N	\N	2025-11-25 21:24:22.491193+00	62.53395932583312	28.014201	{}	2025-11-25 21:23:54.48055+00	2025-11-25 21:24:22.494136+00
b4b1f04f-1b2b-401a-bc72-cf398f3f47af	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.8419934518647	2025-11-25 21:24:58.511991+00	\N	\N	\N	2025-11-25 21:25:20.523596+00	66.11658161785496	22.011605	{}	2025-11-25 21:24:58.514567+00	2025-11-25 21:25:20.525981+00
5b1d8bfc-93c8-4147-b1ed-23cc24f4c3a4	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.88382829802245	2025-11-25 21:49:05.313087+00	\N	\N	\N	2025-11-25 21:49:27.324643+00	65.38594564647615	22.011556	{}	2025-11-25 21:49:05.315331+00	2025-11-25 21:49:27.327286+00
2f71c8bb-c8ef-41bb-b377-ec6ad5a91d88	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.69389872972481	2025-11-25 21:25:58.543871+00	\N	\N	\N	2025-11-25 21:26:26.563241+00	67.92807480627168	28.01937	{}	2025-11-25 21:25:58.701162+00	2025-11-25 21:26:26.566749+00
31371e22-291e-4d79-a728-bd3f7c7b1a77	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.55999479387994	2025-11-25 22:50:55.299916+00	\N	\N	\N	2025-11-25 22:51:17.310832+00	60.93242075006735	22.010916	{}	2025-11-25 22:50:55.302049+00	2025-11-25 22:51:17.358796+00
e7fbf78b-3352-4e9b-9517-74a30076c826	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.13905934710027	2025-11-25 21:27:04.584595+00	\N	\N	\N	2025-11-25 21:27:30.600256+00	65.99704586364875	26.015661	{}	2025-11-25 21:27:04.587366+00	2025-11-25 21:27:30.603203+00
f12fabe0-da5d-4143-8f47-56e7e7358cb5	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.58989664881959	2025-11-25 21:51:09.383195+00	\N	\N	\N	2025-11-25 21:51:35.398169+00	62.79813225972468	26.014974	{}	2025-11-25 21:51:09.385733+00	2025-11-25 21:51:35.400762+00
02d009bd-07c4-4d54-bf23-4bbe1f2ad7c0	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.18753688446353	2025-11-25 21:30:08.689833+00	\N	\N	\N	2025-11-25 21:30:46.713844+00	54.805300873397236	38.024011	{}	2025-11-25 21:30:08.69331+00	2025-11-25 21:30:47.444683+00
97ff3a86-9cc5-4390-ba3c-60957f494007	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.56230439972275	2025-11-25 21:53:15.451961+00	\N	\N	\N	2025-11-25 21:53:41.464602+00	63.07846077252809	26.012641	{}	2025-11-25 21:53:15.503372+00	2025-11-25 21:53:41.46786+00
30b3c773-ab52-4fd6-8526-a3af708e4c84	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.42174240909453	2025-11-25 23:21:10.258948+00	\N	\N	\N	2025-11-25 23:21:38.273698+00	61.95492710135266	28.01475	{}	2025-11-25 23:21:10.264866+00	2025-11-25 23:21:38.275794+00
42b86305-ed7e-4dc2-9933-e8ca651c82b3	968bfc86-180d-454f-8417-09f433813918	CLEARED	79.51429251952771	2025-11-25 22:17:22.222334+00	\N	\N	\N	2025-11-25 22:17:44.23192+00	65.92131136461322	22.009586	{}	2025-11-25 22:17:22.224902+00	2025-11-25 22:17:44.234367+00
b13ba450-533a-492c-825b-ecd7f5e69ced	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.30157804839975	2025-11-25 22:19:24.282741+00	\N	\N	\N	2025-11-25 22:19:56.298935+00	61.825956808407895	32.016194	{}	2025-11-25 22:19:24.285732+00	2025-11-25 22:19:56.301269+00
7df275c6-f761-4d74-acff-23ecd9ec1688	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.35687633448651	2025-11-25 23:22:12.291112+00	\N	\N	\N	2025-11-25 23:22:42.305861+00	60.13235081396029	30.014749	{}	2025-11-25 23:22:12.293693+00	2025-11-25 23:22:42.30821+00
8826f497-f280-46d0-a43d-c8d0d241055b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.23146560351317	2025-11-25 22:21:26.34385+00	\N	\N	\N	2025-11-25 22:21:56.357358+00	62.89847879895846	30.013508	{}	2025-11-25 22:21:26.346262+00	2025-11-25 22:21:56.360272+00
6d3873e5-7e15-4316-b0e3-a33f12ff465b	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.90211177028586	2025-11-25 22:22:36.375828+00	\N	\N	\N	2025-11-25 22:22:56.386938+00	66.9464422788347	20.01111	{}	2025-11-25 22:22:36.378637+00	2025-11-25 22:22:56.390104+00
d3513bd2-eb00-4db2-aa5b-01564febd1c5	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.52162899028976	2025-11-25 23:23:16.322742+00	\N	\N	\N	2025-11-25 23:23:48.340444+00	62.49562187055424	32.017702	{}	2025-11-25 23:23:16.325507+00	2025-11-25 23:23:48.342966+00
f0187144-760e-4560-a0b9-ee43970e7cbe	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.67368637781779	2025-11-25 22:23:34.408297+00	\N	\N	\N	2025-11-25 22:23:58.42173+00	67.46645083215009	24.013433	{}	2025-11-25 22:23:34.411197+00	2025-11-25 22:23:58.424351+00
d093144c-e8f4-408b-beee-30aa54c91049	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.01047575956652	2025-11-25 22:24:38.444657+00	\N	\N	\N	2025-11-25 22:25:06.456033+00	62.653811987179864	28.011376	{}	2025-11-25 22:24:38.447411+00	2025-11-25 22:25:06.459117+00
0d14225f-8fcf-4b2e-9870-0918813e2c4a	968bfc86-180d-454f-8417-09f433813918	CLEARED	79.26446900986817	2025-11-25 23:24:24.359478+00	\N	\N	\N	2025-11-25 23:24:46.370683+00	65.40410819292624	22.011205	{}	2025-11-25 23:24:24.362572+00	2025-11-25 23:24:46.373531+00
7a41a5d1-03cd-491b-9dfb-d9cef5fe0fb0	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.0227395058255	2025-11-25 22:25:36.475352+00	\N	\N	\N	2025-11-25 22:25:38.476907+00	62.16341571808388	2.001555	{}	2025-11-25 22:25:36.542927+00	2025-11-25 22:25:38.47978+00
3ccb56db-adaa-499a-a0c4-dda390ce7833	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.83100747505584	2025-11-25 22:27:50.549471+00	\N	\N	\N	2025-11-25 22:28:14.56166+00	61.46313008861639	24.012189	{}	2025-11-25 22:27:50.551907+00	2025-11-25 22:28:14.564603+00
bcccb2a2-a49e-440e-977d-203a49f35893	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.2949225650762	2025-11-25 22:28:50.582917+00	\N	\N	\N	2025-11-25 22:29:16.59949+00	62.360433251498606	26.016573	{}	2025-11-25 22:28:50.585714+00	2025-11-25 22:29:16.60653+00
ec0d4c62-16be-41f8-a68d-d15367e7b09e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.81747247999455	2025-11-25 22:29:18.601258+00	\N	\N	\N	2025-11-25 22:29:20.60279+00	60.80961353230458	2.001532	{}	2025-11-25 22:29:18.60365+00	2025-11-25 22:29:21.225243+00
049cbff4-d6de-4955-986c-c7e0e910955b	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.55234233588294	2025-11-25 19:24:18.315925+00	\N	\N	\N	2025-11-25 19:24:42.33459+00	64.18060418022127	24.018665	{}	2025-11-25 19:24:18.325263+00	2025-11-25 19:24:42.343961+00
d534edfc-0e90-4c82-8f98-83d0893a270d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.22536380582079	2025-11-25 20:00:51.58085+00	\N	\N	\N	2025-11-25 20:00:53.583794+00	62.19625452573749	2.002944	{}	2025-11-25 20:00:51.585217+00	2025-11-25 20:00:53.592258+00
44e71ee6-ef85-4d5f-8a0f-405305ddbefc	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.30248284818529	2025-11-25 19:37:53.782513+00	\N	\N	\N	2025-11-25 19:38:19.805101+00	66.18296731549746	26.022588	{}	2025-11-25 19:37:53.792801+00	2025-11-25 19:38:20.049961+00
bf5494ba-a38f-433c-9b18-d6dac44778b6	968bfc86-180d-454f-8417-09f433813918	ACTIVE	74.95566709853475	2025-11-25 19:38:59.838181+00	\N	\N	\N	\N	\N	\N	{}	2025-11-25 19:38:59.848314+00	2025-11-25 19:38:59.848314+00
e61c2e6c-141a-448d-adb3-d6b0fef1a9cd	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.77225169939965	2025-11-25 20:58:47.650381+00	\N	\N	\N	2025-11-25 20:59:09.662241+00	66.77137292506862	22.01186	{}	2025-11-25 20:58:47.657601+00	2025-11-25 20:59:09.665781+00
78397873-8cd3-4aba-bd7b-83ada34aa7a3	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.83014294417778	2025-11-25 20:02:03.648251+00	\N	\N	\N	2025-11-25 20:02:23.66253+00	67.22436938270668	20.014279	{}	2025-11-25 20:02:03.65702+00	2025-11-25 20:02:23.668903+00
ea5b6b96-4361-47fd-8acd-3fe680e53249	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	80.55598613691781	2025-11-25 19:40:16.469191+00	\N	\N	\N	2025-11-25 19:40:18.472092+00	76.28627503023145	2.002901	{}	2025-11-25 19:40:16.47254+00	2025-11-25 19:40:18.481996+00
a6a1157c-24d7-4772-a9de-728cd23151f2	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.38371604695554	2025-11-25 19:39:58.446225+00	\N	\N	\N	2025-11-25 19:40:24.480987+00	66.36975523461068	26.034762	{}	2025-11-25 19:39:58.454846+00	2025-11-25 19:40:24.485567+00
58d8b3a2-2faa-4c60-9360-c2fae6cedab3	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.43936607851735	2025-11-25 21:44:53.180812+00	\N	\N	\N	2025-11-25 21:45:19.193393+00	60.35743672536804	26.012581	{}	2025-11-25 21:44:53.260255+00	2025-11-25 21:45:19.201096+00
28b8b450-ef4c-41dd-9d6c-13be17c3d923	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.38261837158052	2025-11-25 20:02:59.696231+00	\N	\N	\N	2025-11-25 20:03:01.702484+00	66.28510213186908	2.006253	{}	2025-11-25 20:02:59.70563+00	2025-11-25 20:03:01.720179+00
cca76530-53a5-471e-bfd1-28bf91f57777	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	80.1869921550558	2025-11-25 19:41:22.544526+00	\N	\N	\N	2025-11-25 19:41:24.550505+00	77.27056950755606	2.005979	{}	2025-11-25 19:41:22.556825+00	2025-11-25 19:41:24.562337+00
20a86a94-cee4-4d60-886f-6dfd405d23d7	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.23127323830653	2025-11-25 19:41:06.521699+00	\N	\N	\N	2025-11-25 19:41:28.558501+00	64.56578358902536	22.036802	{}	2025-11-25 19:41:06.528201+00	2025-11-25 19:41:28.571709+00
79e7895a-144d-486a-931d-9d1792372748	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.54843841295101	2025-11-25 20:59:45.682236+00	\N	\N	\N	2025-11-25 21:00:21.706287+00	57.352319584668386	36.024051	{}	2025-11-25 20:59:46.454045+00	2025-11-25 21:00:21.709777+00
4c28f731-b5ac-4b7e-96b9-b81879df3d13	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.21520504482129	2025-11-25 19:57:41.406774+00	\N	\N	\N	2025-11-25 19:58:15.436833+00	60.679504066530654	34.030059	{}	2025-11-25 19:57:41.411072+00	2025-11-25 19:58:15.44033+00
55ab0d6e-bdf0-4055-bab1-66f7d6fdeb92	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.09824990973911	2025-11-25 20:03:03.711032+00	\N	\N	\N	2025-11-25 20:03:27.728561+00	65.15521956383783	24.017529	{}	2025-11-25 20:03:03.71942+00	2025-11-25 20:03:27.73224+00
59bd08e6-c9a9-4750-a2fe-96d993702e1b	968bfc86-180d-454f-8417-09f433813918	CLEARED	82.91237377747927	2025-11-25 22:44:39.105207+00	\N	\N	\N	2025-11-25 22:45:03.121007+00	60.918202512091085	24.0158	{}	2025-11-25 22:44:39.108387+00	2025-11-25 22:45:03.124271+00
d5d30f59-fc2d-4537-a259-76fcaeb8ee37	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.16337388470558	2025-11-25 21:00:53.723757+00	\N	\N	\N	2025-11-25 21:01:17.735038+00	63.38747603510643	24.011281	{}	2025-11-25 21:00:53.726387+00	2025-11-25 21:01:17.738243+00
5447fe0a-b963-4611-901d-2ceffcbe020c	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.84897593703019	2025-11-25 20:04:07.773842+00	\N	\N	\N	2025-11-25 20:04:27.7933+00	67.13005571961276	20.019458	{}	2025-11-25 20:04:07.783474+00	2025-11-25 20:04:27.802419+00
ee69c222-5472-4154-80bf-9e602b517fbb	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.60916434864365	2025-11-25 20:03:59.755712+00	\N	\N	\N	2025-11-25 20:04:35.80423+00	60.467106660862	36.048518	{}	2025-11-25 20:03:59.762817+00	2025-11-25 20:04:35.81226+00
9e7903c9-8a68-4d0d-886c-dd658afb4c18	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.5107076296207	2025-11-25 21:45:59.213967+00	\N	\N	\N	2025-11-25 21:46:19.225396+00	64.33366590337805	20.011429	{}	2025-11-25 21:45:59.217175+00	2025-11-25 21:46:19.228215+00
9efaff80-acee-4f61-a972-7e26055ba833	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.78934501729837	2025-11-25 21:23:50.473937+00	\N	\N	\N	2025-11-25 21:24:22.49126+00	58.99814778907209	32.017323	{}	2025-11-25 21:23:50.476546+00	2025-11-25 21:24:22.497706+00
0366e00c-75f6-4532-8b69-564d843dec26	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.44207154269341	2025-11-25 21:24:54.507767+00	\N	\N	\N	2025-11-25 21:25:28.528715+00	60.15418975281678	34.020948	{}	2025-11-25 21:24:54.52021+00	2025-11-25 21:25:28.531339+00
e8c19e50-9b3d-41fe-9041-fed9170a0bb0	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.58202153356225	2025-11-25 21:46:57.24563+00	\N	\N	\N	2025-11-25 21:47:23.258964+00	65.35770908793094	26.013334	{}	2025-11-25 21:46:57.25123+00	2025-11-25 21:47:23.261418+00
fbf1a582-161c-4610-b87c-fa97bf603b05	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.41027051724666	2025-11-25 21:25:56.541747+00	\N	\N	\N	2025-11-25 21:26:28.566185+00	60.837121781007085	32.024438	{}	2025-11-25 21:25:56.544598+00	2025-11-25 21:26:28.568589+00
2bfd67d1-4781-47dd-8eaf-d0eb40dbb7b0	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.19072137510443	2025-11-25 22:46:43.173147+00	\N	\N	\N	2025-11-25 22:48:03.210916+00	67.97166878999306	80.037769	{}	2025-11-25 22:46:43.259963+00	2025-11-25 22:48:03.213826+00
a6f0157f-e4b0-4bf8-bb40-23480a6c4b8f	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.98340378902034	2025-11-25 21:26:58.581448+00	\N	\N	\N	2025-11-25 21:27:30.600323+00	62.892269690796354	32.018875	{}	2025-11-25 21:26:58.584703+00	2025-11-25 21:27:30.608319+00
393cca92-b604-40ee-8037-d97f3d402fcd	968bfc86-180d-454f-8417-09f433813918	CLEARED	80.63861486884552	2025-11-25 21:55:23.525029+00	\N	\N	\N	2025-11-25 21:55:51.537753+00	59.7842400751839	28.012724	{}	2025-11-25 21:55:23.751802+00	2025-11-25 21:55:51.540034+00
430d4b54-2ee0-4c6e-b8a5-c6c0c20bf57f	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.1557846662004	2025-11-25 21:28:06.616403+00	\N	\N	\N	2025-11-25 21:28:30.632378+00	65.65179928753456	24.015975	{}	2025-11-25 21:28:07.074434+00	2025-11-25 21:28:30.635177+00
00e1c1ae-4176-499c-96b5-39a3ea6e2320	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.14906938915104	2025-11-25 21:29:06.649539+00	\N	\N	\N	2025-11-25 21:29:40.67439+00	60.93391132145639	34.024851	{}	2025-11-25 21:29:06.658368+00	2025-11-25 21:29:40.677051+00
2b2c2abf-4e52-4c4a-ba0c-a47128c7472c	968bfc86-180d-454f-8417-09f433813918	CLEARED	80.95182615418223	2025-11-25 22:18:26.25667+00	\N	\N	\N	2025-11-25 22:18:50.267726+00	64.37769481368728	24.011056	{}	2025-11-25 22:18:26.258848+00	2025-11-25 22:18:50.270391+00
0e8f8bb8-8f5a-428e-87a0-2710aeb6d13b	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.68580842368502	2025-11-25 22:48:43.231732+00	\N	\N	\N	2025-11-25 22:49:07.246993+00	66.43744525279406	24.015261	{}	2025-11-25 22:48:43.234342+00	2025-11-25 22:49:07.249433+00
d47d75ea-7666-4e75-919f-f85d72f2332f	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.08667634966514	2025-11-25 22:19:24.282665+00	\N	\N	\N	2025-11-25 22:19:50.296213+00	65.7051913522945	26.013548	{}	2025-11-25 22:19:24.289116+00	2025-11-25 22:19:50.298864+00
d644743a-3798-4a55-99df-b47c1a3f80d4	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.77608096722926	2025-11-25 22:20:28.314375+00	\N	\N	\N	2025-11-25 22:20:58.329477+00	58.05204198452778	30.015102	{}	2025-11-25 22:20:28.317406+00	2025-11-25 22:20:58.337541+00
915c5654-deac-4740-91f6-f81cd8f9100a	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.4849094825741	2025-11-25 22:49:45.26395+00	\N	\N	\N	2025-11-25 22:50:13.276269+00	67.25131501044237	28.012319	{}	2025-11-25 22:49:45.266368+00	2025-11-25 22:50:13.279374+00
1f2c6639-b168-4172-a1c3-87fb5a075cd6	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.23443560857942	2025-11-25 22:22:36.375914+00	\N	\N	\N	2025-11-25 22:23:06.391905+00	58.389963956428694	30.015991	{}	2025-11-25 22:22:36.383932+00	2025-11-25 22:23:06.394727+00
db4d3fed-9965-4a1b-8f06-bfb701cd5d1a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.39144677289421	2025-11-25 22:23:34.408378+00	\N	\N	\N	2025-11-25 22:24:04.425308+00	60.22488888523745	30.01693	{}	2025-11-25 22:23:34.415847+00	2025-11-25 22:24:04.427861+00
8a27471c-0ff4-4e93-b16b-0e357bec3670	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.18617324706807	2025-11-25 22:51:45.327986+00	\N	\N	\N	2025-11-25 22:52:29.352586+00	57.94051272141473	44.0246	{}	2025-11-25 22:51:45.330408+00	2025-11-25 22:52:29.355155+00
4cb3505c-ca28-47e1-81e9-aec956b2bc95	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.61567416368949	2025-11-25 22:27:42.541651+00	\N	\N	\N	2025-11-25 22:28:18.565964+00	57.253823904604566	36.024313	{}	2025-11-25 22:27:42.544257+00	2025-11-25 22:28:18.568243+00
f783c213-9f46-4236-b449-4dfdce04f446	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.12509844923798	2025-11-25 22:29:54.618322+00	\N	\N	\N	2025-11-25 22:30:16.631115+00	65.57746123364808	22.012793	{}	2025-11-25 22:29:54.621262+00	2025-11-25 22:30:16.634644+00
20132ae0-ab95-4284-9b69-537f9e287425	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.41207139460269	2025-11-25 22:52:51.365476+00	\N	\N	\N	2025-11-25 22:53:27.381981+00	57.33163764895202	36.016505	{}	2025-11-25 22:52:51.367881+00	2025-11-25 22:53:27.384545+00
2e5151db-83d5-4c1a-83ed-28879e3f6723	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.89515577842093	2025-11-25 22:54:59.436389+00	\N	\N	\N	2025-11-25 22:55:33.45347+00	58.117241233998016	34.017081	{}	2025-11-25 22:54:59.43929+00	2025-11-25 22:55:33.95809+00
4122b913-9c60-4e27-93d3-fc8ee9aceb77	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.43835226710942	2025-11-25 22:56:03.468951+00	\N	\N	\N	2025-11-25 22:56:31.48483+00	65.45673751005432	28.015879	{}	2025-11-25 22:56:03.471825+00	2025-11-25 22:56:31.487349+00
dd84ccf1-f0f8-48e3-8ba2-d1d08bb61636	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	76.28343457062593	2025-11-25 22:57:07.50212+00	\N	\N	\N	2025-11-25 22:57:37.518739+00	58.76510256143631	30.016619	{}	2025-11-25 22:57:07.509203+00	2025-11-25 22:57:37.52626+00
366d7e18-c7f2-4208-83e3-33170847d113	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.80199205559423	2025-11-25 23:21:40.275831+00	\N	\N	\N	2025-11-25 23:21:44.277667+00	56.34547675525899	4.001836	{}	2025-11-25 23:21:40.278194+00	2025-11-25 23:21:44.279981+00
b08c5b34-341a-4250-8be9-103b1dd54b65	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.63030680541078	2025-11-25 23:22:12.29102+00	\N	\N	\N	2025-11-25 23:22:40.304804+00	66.73498461995104	28.013784	{}	2025-11-25 23:22:12.299292+00	2025-11-25 23:22:40.307072+00
a571eaa2-49e1-461b-911b-7f330aed12f5	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.28524859541905	2025-11-25 23:23:18.325197+00	\N	\N	\N	2025-11-25 23:23:48.340535+00	55.14914956291143	30.015338	{}	2025-11-25 23:23:18.327554+00	2025-11-25 23:23:48.360356+00
cb0e9f55-fc66-4f6f-8b3c-e8f0ebf4c1f4	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.64273512328973	2025-11-25 19:25:22.364746+00	\N	\N	\N	2025-11-25 19:25:46.383969+00	63.73981881955592	24.019223	{}	2025-11-25 19:25:22.375532+00	2025-11-25 19:25:46.393751+00
df70035b-ca04-4320-bd41-61e149279f39	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.8758879760608	2025-11-25 20:00:57.590325+00	\N	\N	\N	2025-11-25 20:01:21.608096+00	65.22667276629011	24.017771	{}	2025-11-25 20:00:57.593883+00	2025-11-25 20:01:22.410888+00
54c737b6-e85e-4666-8650-76bf4e79929b	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.97402260821964	2025-11-25 19:26:26.414359+00	\N	\N	\N	2025-11-25 19:26:50.436439+00	60.59821808800834	24.02208	{}	2025-11-25 19:26:26.425023+00	2025-11-25 19:26:50.446103+00
e430a9a7-5611-4913-8920-085f66d78607	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.0862366814988	2025-11-25 20:59:41.677808+00	\N	\N	\N	2025-11-25 20:59:43.679284+00	58.92204137501754	2.001476	{}	2025-11-25 20:59:41.680879+00	2025-11-25 20:59:43.682514+00
43c1a430-3366-466c-a1e9-178356573b39	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.06863861281792	2025-11-25 19:28:26.515531+00	\N	\N	\N	2025-11-25 19:28:56.540973+00	61.39566959685299	30.025442	{}	2025-11-25 19:28:26.526302+00	2025-11-25 19:28:57.413172+00
90ca866d-a875-4f42-8507-5d2cf5c8ee80	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.40894159322681	2025-11-25 20:01:59.643211+00	\N	\N	\N	2025-11-25 20:02:27.674447+00	62.66002807350839	28.031236	{}	2025-11-25 20:01:59.651171+00	2025-11-25 20:02:27.68951+00
529a94b8-569e-4b0c-bf85-257a1aca13bd	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.67872869119114	2025-11-25 19:31:39.481096+00	\N	\N	\N	2025-11-25 19:32:03.501505+00	65.49918752752426	24.020409	{}	2025-11-25 19:31:39.491048+00	2025-11-25 19:32:03.510048+00
71d3024f-8772-48a8-b525-18643feaef61	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.47374153850456	2025-11-25 21:48:01.276822+00	\N	\N	\N	2025-11-25 21:48:25.290397+00	64.02392371347707	24.013575	{}	2025-11-25 21:48:01.279904+00	2025-11-25 21:48:25.293079+00
977c8d83-1fff-4970-9196-cd9a6300d06b	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.79951668436154	2025-11-25 19:32:45.535214+00	\N	\N	\N	2025-11-25 19:33:07.554621+00	66.67004979887572	22.019407	{}	2025-11-25 19:32:45.544116+00	2025-11-25 19:33:07.560707+00
dc6ea99b-66bf-4bd4-bec7-8533f2c79dc3	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.62725269934298	2025-11-25 20:04:03.76138+00	\N	\N	\N	2025-11-25 20:04:05.76801+00	66.68230355766782	2.00663	{}	2025-11-25 20:04:03.770857+00	2025-11-25 20:04:05.776214+00
0d7488e5-3043-49d5-9223-206ca608ada6	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.15271957825543	2025-11-25 19:33:51.585004+00	\N	\N	\N	2025-11-25 19:34:09.600384+00	64.98628656152445	18.01538	{}	2025-11-25 19:33:51.59561+00	2025-11-25 19:34:09.603969+00
e84064a8-a427-4287-a431-f59be8f757ca	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.10846175620564	2025-11-25 21:01:51.752328+00	\N	\N	\N	2025-11-25 21:02:21.768281+00	62.61248518497033	30.015953	{}	2025-11-25 21:01:51.755367+00	2025-11-25 21:02:21.776837+00
3d1231c0-e498-4fd3-bf06-7d519ad35ad4	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.60998867352995	2025-11-25 19:34:47.627652+00	\N	\N	\N	2025-11-25 19:35:09.649453+00	65.88304720827796	22.021801	{}	2025-11-25 19:34:47.6367+00	2025-11-25 19:35:09.654266+00
c5c85960-ae98-46bc-b2b6-0dba80cfbde7	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.2075477623543	2025-11-25 20:05:07.830471+00	\N	\N	\N	2025-11-25 20:05:35.851756+00	61.906046899389246	28.021285	{}	2025-11-25 20:05:07.834374+00	2025-11-25 20:05:35.859506+00
5d2943b5-674f-4ff5-8135-703f556741ff	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.35577040541611	2025-11-25 19:36:53.739427+00	\N	\N	\N	2025-11-25 19:37:17.755817+00	65.9988195415142	24.01639	{}	2025-11-25 19:36:53.747625+00	2025-11-25 19:37:17.764271+00
910feea0-5969-40b2-b182-56f7447f386d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.37145086361355	2025-11-25 22:45:29.13337+00	\N	\N	\N	2025-11-25 22:46:07.153866+00	57.225604731919205	38.020496	{}	2025-11-25 22:45:29.135641+00	2025-11-25 22:46:07.156775+00
9c670cc4-212a-40a1-8741-4d164e5b2394	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.49445594114792	2025-11-25 19:39:18.411172+00	\N	\N	\N	2025-11-25 19:39:22.420439+00	64.65477956929291	4.009267	{}	2025-11-25 19:39:18.42376+00	2025-11-25 19:39:22.425801+00
06b62d97-7db2-4ef0-ad1c-f070a0da4a27	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.2950378699633	2025-11-25 20:06:05.873568+00	\N	\N	\N	2025-11-25 20:06:43.904048+00	53.91611445031412	38.03048	{}	2025-11-25 20:06:05.879752+00	2025-11-25 20:06:43.912888+00
d1652480-be78-4bc9-93ff-1c3ed8fe5980	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.67755902247464	2025-11-25 19:41:00.511223+00	\N	\N	\N	2025-11-25 19:41:02.51485+00	67.3128384097109	2.003627	{}	2025-11-25 19:41:00.74658+00	2025-11-25 19:41:02.524679+00
132ae073-2b13-4883-b049-c807a0dda52c	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.51016331021198	2025-11-25 21:31:12.728727+00	\N	\N	\N	2025-11-25 21:31:44.747796+00	56.22642864410673	32.019069	{}	2025-11-25 21:31:12.732065+00	2025-11-25 21:31:44.750402+00
81e919d1-1bf8-412d-970e-1284df4b786c	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	80.09973557755613	2025-11-25 19:41:10.526368+00	\N	\N	\N	2025-11-25 19:41:18.53775+00	76.55962612962281	8.011382	{}	2025-11-25 19:41:10.543019+00	2025-11-25 19:41:18.547617+00
cac060d0-eba0-4e6b-b220-9a68d017b6f6	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.99988856453506	2025-11-25 21:49:01.31036+00	\N	\N	\N	2025-11-25 21:49:31.328576+00	62.26134907192309	30.018216	{}	2025-11-25 21:49:01.313412+00	2025-11-25 21:49:31.331113+00
44ffa8c1-8d2c-4d58-b5e8-007a4dbf2768	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.61936053046577	2025-11-25 21:32:16.767251+00	\N	\N	\N	2025-11-25 21:32:46.783575+00	57.537506566835845	30.016324	{}	2025-11-25 21:32:16.770405+00	2025-11-25 21:32:46.792976+00
1dad722f-a414-4b2e-bedd-39d293a88319	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.12132288791176	2025-11-25 21:33:18.800009+00	\N	\N	\N	2025-11-25 21:33:52.818218+00	56.95702942641211	34.018209	{}	2025-11-25 21:33:18.805949+00	2025-11-25 21:33:52.821355+00
55a2d0ed-fbf4-4bc7-8ded-e4db9747e424	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.42540998835719	2025-11-25 21:50:05.349049+00	\N	\N	\N	2025-11-25 21:50:31.361291+00	67.02280637853674	26.012242	{}	2025-11-25 21:50:05.352221+00	2025-11-25 21:50:31.364635+00
0e52f059-a328-4088-92d6-ee53a60bba59	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.86895460751701	2025-11-25 21:34:22.834226+00	\N	\N	\N	2025-11-25 21:34:48.847803+00	61.42246384541332	26.013577	{}	2025-11-25 21:34:22.841575+00	2025-11-25 21:34:48.850748+00
2b56e485-d9f4-4d97-9665-a916d2e0319e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.98790748582564	2025-11-25 22:46:37.170361+00	\N	\N	\N	2025-11-25 22:47:09.186155+00	56.00467352652001	32.015794	{}	2025-11-25 22:46:37.172863+00	2025-11-25 22:47:09.188609+00
b52d7d28-1d07-46a7-8efc-ea4bca0f96ac	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.78700424881964	2025-11-25 21:51:01.377305+00	\N	\N	\N	2025-11-25 21:51:41.401585+00	55.50826015360106	40.02428	{}	2025-11-25 21:51:01.380052+00	2025-11-25 21:51:41.405127+00
163d2e95-e9e7-4ef0-8b92-2d72f681b775	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.74449085801692	2025-11-25 21:52:09.41346+00	\N	\N	\N	2025-11-25 21:52:39.429731+00	59.596113938265745	30.016271	{}	2025-11-25 21:52:09.421846+00	2025-11-25 21:52:39.432112+00
04f0f19b-6b29-46c1-b0e4-ddd79a4e58b9	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.18238390247764	2025-11-25 22:53:55.398898+00	\N	\N	\N	2025-11-25 22:54:29.419791+00	60.64787563040547	34.020893	{}	2025-11-25 22:53:55.401412+00	2025-11-25 22:54:29.825722+00
df267075-7f81-40bf-adfe-2fd26ea7daf6	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.03840615435212	2025-11-25 21:54:21.489114+00	\N	\N	\N	2025-11-25 21:54:43.497771+00	66.32719308108915	22.008657	{}	2025-11-25 21:54:21.49243+00	2025-11-25 21:54:43.499957+00
b6fa65aa-b09f-403b-9104-557ea3ca354b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.73242959062684	2025-11-25 22:30:54.653353+00	\N	\N	\N	2025-11-25 22:31:24.673833+00	61.77718097599392	30.02048	{}	2025-11-25 22:30:54.65667+00	2025-11-25 22:31:24.676078+00
6ff3448d-4234-49d3-8d6e-a68019b3bf7a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.29573188033646	2025-11-25 23:25:22.390135+00	\N	\N	\N	2025-11-25 23:25:58.408888+00	54.11037390888642	36.018753	{}	2025-11-25 23:25:22.398934+00	2025-11-25 23:25:58.411407+00
006ebfbf-a5c3-44ec-aee5-676cc6d67617	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.18438784579625	2025-11-25 22:32:00.695345+00	\N	\N	\N	2025-11-25 22:32:26.711163+00	67.89898983608394	26.015818	{}	2025-11-25 22:32:00.698174+00	2025-11-25 22:32:26.7138+00
51f5ab55-5942-4f18-bc76-9f03167dec17	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.61556438168513	2025-11-25 22:33:04.736039+00	\N	\N	\N	2025-11-25 22:33:24.748298+00	66.36730704285908	20.012259	{}	2025-11-25 22:33:04.738328+00	2025-11-25 22:33:24.751183+00
ca14d813-e9ef-45ca-851e-ae5f8177abe6	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.40883493702648	2025-11-25 23:26:28.426864+00	\N	\N	\N	2025-11-25 23:26:50.437496+00	66.15741260697962	22.010632	{}	2025-11-25 23:26:28.429601+00	2025-11-25 23:26:50.699643+00
10d9d4c5-e191-40d6-8499-5ba1c89a2804	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.99512642171463	2025-11-25 22:33:58.769207+00	\N	\N	\N	2025-11-25 22:34:34.78638+00	61.97468062293137	36.017173	{}	2025-11-25 22:33:58.772047+00	2025-11-25 22:34:34.78846+00
34a298a9-74a1-42d1-ab92-23a72eb74509	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.27784276677814	2025-11-25 23:27:32.46208+00	\N	\N	\N	2025-11-25 23:27:56.475533+00	59.573831629770304	24.013453	{}	2025-11-25 23:27:32.471314+00	2025-11-25 23:27:56.478155+00
9d375fbd-1a19-4e2e-b1fb-c0ed33f2a28b	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.35842064529928	2025-11-25 19:30:36.61221+00	\N	\N	\N	2025-11-25 19:31:02.635147+00	66.58700043721232	26.022937	{}	2025-11-25 19:30:36.620196+00	2025-11-25 19:31:02.641821+00
2ca2994c-eaa2-45e3-9fbd-09bbcba3bf26	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.25469974203828	2025-11-25 20:06:13.881273+00	\N	\N	\N	2025-11-25 20:06:37.898865+00	67.11061961963668	24.017592	{}	2025-11-25 20:06:13.892173+00	2025-11-25 20:06:37.903172+00
4a6024fb-a7eb-4c2f-b1a9-1e31de84b0e3	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.28139800116266	2025-11-25 19:36:49.728121+00	\N	\N	\N	2025-11-25 19:36:51.733136+00	66.81000188190325	2.005015	{}	2025-11-25 19:36:49.73784+00	2025-11-25 19:36:51.742295+00
3b41e83b-27ec-48f6-bb89-7c25ef3ee761	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.06502009666929	2025-11-25 20:59:45.682143+00	\N	\N	\N	2025-11-25 20:59:49.685213+00	65.96515328563535	4.00307	{}	2025-11-25 20:59:46.468031+00	2025-11-25 20:59:49.688391+00
ca0f1dd5-b612-4e56-b637-260ea81288c9	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.1363359012133	2025-11-25 20:07:11.926034+00	\N	\N	\N	2025-11-25 20:07:43.951717+00	60.07876127946543	32.025683	{}	2025-11-25 20:07:11.936241+00	2025-11-25 20:07:43.957666+00
2d581a14-f0b6-4cd6-92ea-277a74ad5d8f	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.28647391038207	2025-11-25 21:50:01.346704+00	\N	\N	\N	2025-11-25 21:50:33.36486+00	59.69820954664212	32.018156	{}	2025-11-25 21:50:01.349419+00	2025-11-25 21:50:33.367705+00
b611cfa5-6919-419d-9861-978150418e5b	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.39168220884973	2025-11-25 20:22:07.121776+00	\N	\N	\N	2025-11-25 20:22:33.155734+00	62.9760960003918	26.033958	{}	2025-11-25 20:22:07.155742+00	2025-11-25 20:22:34.02869+00
13f04a2b-cd01-4935-a29e-4ed726fdda58	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	ACTIVE	75.99857675497827	2025-11-25 20:23:11.200782+00	\N	\N	\N	\N	\N	\N	{}	2025-11-25 20:23:11.215646+00	2025-11-25 20:23:11.215646+00
f11797f9-c7fc-4a9b-8331-f41476a7b386	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.24209624372389	2025-11-25 21:31:16.731162+00	\N	\N	\N	2025-11-25 21:31:36.741859+00	67.18873553397539	20.010697	{}	2025-11-25 21:31:16.734497+00	2025-11-25 21:31:36.744807+00
a520ffea-ef3a-4c37-8958-b6bb34884c58	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.7872864333731	2025-11-25 20:30:24.639087+00	\N	\N	\N	2025-11-25 20:30:56.721956+00	62.299447652876125	32.082869	{}	2025-11-25 20:30:24.683694+00	2025-11-25 20:30:56.735638+00
a6cd5fa4-88ac-4d77-8354-79cd7cca3bae	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.52492748199103	2025-11-25 22:45:35.138796+00	\N	\N	\N	2025-11-25 22:46:01.150298+00	64.92013746322512	26.011502	{}	2025-11-25 22:45:35.141363+00	2025-11-25 22:46:01.152689+00
23947c0e-baa3-44f5-95df-38d3421563e6	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.31571397080197	2025-11-25 20:31:32.750094+00	\N	\N	\N	2025-11-25 20:31:56.762447+00	66.84949250728167	24.012353	{}	2025-11-25 20:31:32.754917+00	2025-11-25 20:31:57.254827+00
bdca61f4-a454-422d-bd67-ffb5eeaa52f0	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.64315966862655	2025-11-25 21:34:50.849828+00	\N	\N	\N	2025-11-25 21:34:52.852119+00	58.94671531755401	2.002291	{}	2025-11-25 21:34:50.852776+00	2025-11-25 21:34:52.854472+00
ef3a93af-1680-436a-91e4-4e5c5f1f6784	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.82200311145354	2025-11-25 20:32:36.785073+00	\N	\N	\N	2025-11-25 20:33:02.798873+00	62.04466744715575	26.0138	{}	2025-11-25 20:32:36.78874+00	2025-11-25 20:33:02.803308+00
33b406d9-4972-4d46-905f-7bb18fe00a10	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.51726679734239	2025-11-25 21:52:09.41338+00	\N	\N	\N	2025-11-25 21:52:37.427099+00	67.10237790292743	28.013719	{}	2025-11-25 21:52:09.41619+00	2025-11-25 21:52:37.430136+00
26aaddcc-8fb3-4e4a-ba45-88cb8b7b3029	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.55862904364804	2025-11-25 20:39:51.019717+00	\N	\N	\N	2025-11-25 20:40:25.040958+00	56.641290492268844	34.021241	{}	2025-11-25 20:39:51.023425+00	2025-11-25 20:40:25.044469+00
0c4244f0-6e68-4726-ab6c-03158bbc4035	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.92926699336378	2025-11-25 21:36:22.902275+00	\N	\N	\N	2025-11-25 21:37:00.92567+00	55.8265746889985	38.023395	{}	2025-11-25 21:36:22.904819+00	2025-11-25 21:37:00.928725+00
cdc6c058-f778-4453-9c31-5a785a1a98ca	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.90141627453932	2025-11-25 20:41:55.090118+00	\N	\N	\N	2025-11-25 20:42:35.112217+00	60.15782668966572	40.022099	{}	2025-11-25 20:41:55.093055+00	2025-11-25 20:42:35.115769+00
1552b343-79e7-4265-9fa3-8c81709ee04b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.24709649387097	2025-11-25 20:44:05.162798+00	\N	\N	\N	2025-11-25 20:44:41.185511+00	54.49207924943957	36.022713	{}	2025-11-25 20:44:05.166547+00	2025-11-25 20:44:41.188319+00
d4c45363-d59b-4122-9c76-78784cbb02d3	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.72004711260708	2025-11-25 21:53:11.449487+00	\N	\N	\N	2025-11-25 21:53:49.46833+00	54.937677629965954	38.018843	{}	2025-11-25 21:53:11.452415+00	2025-11-25 21:53:49.471508+00
4d96aed9-1353-44ab-9d86-1f320d7191f9	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	74.62473383384847	2025-11-25 20:45:09.201851+00	\N	\N	\N	2025-11-25 20:45:39.219793+00	59.525307517396655	30.017942	{}	2025-11-25 20:45:09.205361+00	2025-11-25 20:45:39.223288+00
af3d3030-0b36-46d6-b42c-1e763731275b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.48773850725021	2025-11-25 22:48:43.231809+00	\N	\N	\N	2025-11-25 22:49:11.249457+00	62.60393133154301	28.017648	{}	2025-11-25 22:48:43.236764+00	2025-11-25 22:49:11.251985+00
446ce649-fbea-41b0-b2ab-730ad729aa7b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.26418132204186	2025-11-25 20:46:07.234071+00	\N	\N	\N	2025-11-25 20:46:41.255082+00	58.50159970327586	34.021011	{}	2025-11-25 20:46:08.015777+00	2025-11-25 20:46:41.257866+00
a0c883a0-73a9-4f90-95ab-aa10414fcb32	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.20996063268157	2025-11-25 21:54:13.484157+00	\N	\N	\N	2025-11-25 21:54:49.501863+00	62.279948462777284	36.017706	{}	2025-11-25 21:54:13.487069+00	2025-11-25 21:54:49.504858+00
8215b49c-e594-4f8a-8d63-eb89cd2f1b5d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.21574489675434	2025-11-25 21:55:19.522057+00	\N	\N	\N	2025-11-25 21:55:47.53514+00	61.92390568519538	28.013083	{}	2025-11-25 21:55:19.525027+00	2025-11-25 21:55:47.53802+00
45801d8e-179d-410f-abb1-f15ef5fae8d5	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.07268720563916	2025-11-25 22:49:45.264024+00	\N	\N	\N	2025-11-25 22:50:17.278818+00	58.47401246566915	32.014794	{}	2025-11-25 22:49:45.269394+00	2025-11-25 22:50:17.28109+00
83893ba9-24d9-4619-8ccc-63d5554bd5f0	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.25657519592025	2025-11-25 22:31:00.657201+00	\N	\N	\N	2025-11-25 22:31:18.669037+00	66.73211632255729	18.011836	{}	2025-11-25 22:31:00.65963+00	2025-11-25 22:31:18.672056+00
243bb671-4b63-4ba9-a76e-7287038160b6	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.9845621789532	2025-11-25 22:34:04.772153+00	\N	\N	\N	2025-11-25 22:34:28.782749+00	64.54508452899455	24.010596	{}	2025-11-25 22:34:04.774631+00	2025-11-25 22:34:28.785127+00
c8b5e765-f3e4-461b-a2d4-7d387ce7b6ec	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.88154579052298	2025-11-25 22:50:45.292979+00	\N	\N	\N	2025-11-25 22:51:19.31331+00	57.42929608564696	34.020331	{}	2025-11-25 22:50:45.300764+00	2025-11-25 22:51:19.315663+00
535655ac-9f2b-44b8-a4b3-5554b5e269c0	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.19595379153569	2025-11-25 22:51:53.333194+00	\N	\N	\N	2025-11-25 22:52:23.349137+00	60.72439125146846	30.015943	{}	2025-11-25 22:51:53.335894+00	2025-11-25 22:52:23.351736+00
90bd696c-7a2c-4316-97cb-2850ebbdd3d2	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.68111829764952	2025-11-25 22:52:53.366882+00	\N	\N	\N	2025-11-25 22:53:23.378236+00	61.874503700588306	30.011354	{}	2025-11-25 22:52:53.646808+00	2025-11-25 22:53:23.381076+00
a800ea3d-eb57-441c-a5a6-f6eec53d0754	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.66639298014995	2025-11-25 22:53:57.400263+00	\N	\N	\N	2025-11-25 22:54:25.416387+00	66.11392150434074	28.016124	{}	2025-11-25 22:53:57.763997+00	2025-11-25 22:54:25.419422+00
35417540-7c35-4bf4-9091-d6719079a800	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.77000629777315	2025-11-25 22:55:05.44067+00	\N	\N	\N	2025-11-25 22:55:43.460001+00	52.93120026420371	38.019331	{}	2025-11-25 22:55:05.443264+00	2025-11-25 22:55:43.462303+00
2a2d7fd7-f6eb-478f-b231-b77f1c18b197	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.06346970097074	2025-11-25 22:55:59.466398+00	\N	\N	\N	2025-11-25 22:56:33.486782+00	57.87836505481346	34.020384	{}	2025-11-25 22:55:59.468991+00	2025-11-25 22:56:33.489235+00
3a212dc8-616b-4704-bedb-54e73098e0f1	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.02719173895085	2025-11-25 22:57:07.502042+00	\N	\N	\N	2025-11-25 22:57:37.51866+00	60.61383765156954	30.016618	{}	2025-11-25 22:57:07.504653+00	2025-11-25 22:57:37.521325+00
a336eb05-3034-488a-9675-92173f43ff80	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.51997033618508	2025-11-25 23:28:26.493107+00	\N	\N	\N	2025-11-25 23:29:00.512437+00	59.08011417454328	34.01933	{}	2025-11-25 23:28:26.966991+00	2025-11-25 23:29:00.515162+00
ecdb7c61-2fa4-4f89-95a3-9e9d9267bab6	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	ACTIVE	67.20278295689357	2025-11-25 23:29:28.526158+00	\N	\N	\N	\N	\N	\N	{}	2025-11-25 23:29:28.529415+00	2025-11-25 23:29:28.529415+00
b00cf38e-e8bd-4316-a3cf-15943bf04cbf	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.28042553957656	2025-11-25 19:42:06.591147+00	\N	\N	\N	2025-11-25 19:42:32.619517+00	62.752049286064405	26.02837	{}	2025-11-25 19:42:06.604415+00	2025-11-25 19:42:32.629348+00
c35a1d28-c186-4f34-a4fe-09d8b4b94098	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.76311238927985	2025-11-25 20:22:07.121931+00	\N	\N	\N	2025-11-25 20:22:35.180666+00	62.47175267188656	28.058735	{}	2025-11-25 20:22:07.1667+00	2025-11-25 20:22:35.188852+00
926b42c8-9efe-4cbb-b733-1aad99a7de21	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	81.33183995438239	2025-11-25 19:43:14.655062+00	\N	\N	\N	2025-11-25 19:43:16.657422+00	75.46254981875578	2.00236	{}	2025-11-25 19:43:14.658921+00	2025-11-25 19:43:16.662157+00
6dd33911-3581-4db3-b8a3-801ec5ca7dcb	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.79118675903246	2025-11-25 21:02:23.770697+00	\N	\N	\N	2025-11-25 21:02:25.773652+00	55.319288028155434	2.002955	{}	2025-11-25 21:02:23.774541+00	2025-11-25 21:02:25.77662+00
0150a96f-eca2-483d-ba7c-ae8926879539	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.13083511872371	2025-11-25 19:44:08.694752+00	\N	\N	\N	2025-11-25 19:44:36.732175+00	64.48545762500558	28.037423	{}	2025-11-25 19:44:08.703215+00	2025-11-25 19:44:36.741085+00
5fa902d6-87be-46c9-8e87-4e96eec95996	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.71216787418842	2025-11-25 20:30:28.673512+00	\N	\N	\N	2025-11-25 20:30:58.730831+00	66.59836764454691	30.057319	{}	2025-11-25 20:30:28.719969+00	2025-11-25 20:30:58.737359+00
c502dec0-ca1b-45b7-8f3d-e4c273f502f5	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	75.1988332656984	2025-11-25 19:46:20.826922+00	\N	\N	\N	2025-11-25 19:46:38.842181+00	72.22697947652908	18.015259	{}	2025-11-25 19:46:20.846697+00	2025-11-25 19:46:38.851059+00
8e5879b4-d208-4aab-be46-4280252d6c67	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.22132060422997	2025-11-25 21:56:21.553976+00	\N	\N	\N	2025-11-25 21:56:49.566782+00	62.83793165322993	28.012806	{}	2025-11-25 21:56:21.557125+00	2025-11-25 21:56:49.569383+00
6d23ea3a-d081-4911-8cf6-417016996eb0	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.00005695806948	2025-11-25 19:48:24.921963+00	\N	\N	\N	2025-11-25 19:48:46.941436+00	66.14372043446161	22.019473	{}	2025-11-25 19:48:24.926296+00	2025-11-25 19:48:46.949791+00
8721e83a-56f3-4562-9ca6-d6dfe91c63eb	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.81219839134306	2025-11-25 20:37:44.946328+00	\N	\N	\N	2025-11-25 20:38:22.970855+00	57.07446996030705	38.024527	{}	2025-11-25 20:37:44.953423+00	2025-11-25 20:38:22.974344+00
636eb2af-8ea1-44e0-b25b-e3c00b488a3d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	75.70444845330256	2025-11-25 19:49:30.979427+00	\N	\N	\N	2025-11-25 19:49:50.998026+00	67.06255217529876	20.018599	{}	2025-11-25 19:49:30.990103+00	2025-11-25 19:49:51.143594+00
16bc568b-c2ee-4d11-bf1f-3c96f7df9037	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.97372066491019	2025-11-25 21:02:55.787009+00	\N	\N	\N	2025-11-25 21:03:31.808218+00	51.04058291129806	36.021209	{}	2025-11-25 21:02:55.790693+00	2025-11-25 21:03:31.811247+00
10438adf-2c29-4dd0-82a0-ecb644e4a67a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.13560334883549	2025-11-25 19:52:31.144766+00	\N	\N	\N	2025-11-25 19:53:05.184861+00	62.90465713133091	34.040095	{}	2025-11-25 19:52:31.926766+00	2025-11-25 19:53:05.191579+00
6d5e0bfa-6fd7-4bda-b0fa-2bc09f55c59d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.05692763818539	2025-11-25 20:38:46.981786+00	\N	\N	\N	2025-11-25 20:39:25.005547+00	60.35939388032939	38.023761	{}	2025-11-25 20:38:46.985687+00	2025-11-25 20:39:25.00956+00
adae0818-eb77-43e4-b5be-1aee5756e0e5	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	74.82781099854184	2025-11-25 19:53:37.206682+00	\N	\N	\N	2025-11-25 19:54:05.230924+00	59.392976511403795	28.024242	{}	2025-11-25 19:53:37.211304+00	2025-11-25 19:54:05.241995+00
16fe82dd-fb58-415d-9180-f7e79db93387	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.10456445458135	2025-11-25 22:58:05.531832+00	\N	\N	\N	2025-11-25 22:58:35.549228+00	61.549356379992574	30.017396	{}	2025-11-25 22:58:05.534465+00	2025-11-25 22:58:35.551603+00
a5642377-fc89-4346-8564-ec3623f0d536	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.25134170080425	2025-11-25 20:40:55.055369+00	\N	\N	\N	2025-11-25 20:41:27.076333+00	58.127570944745685	32.020964	{}	2025-11-25 20:40:55.059473+00	2025-11-25 20:41:27.079376+00
212cd109-c6e2-4cd6-8863-5ae48983bd4d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.61491376075402	2025-11-25 21:05:01.856226+00	\N	\N	\N	2025-11-25 21:05:31.877561+00	60.978670241646824	30.021335	{}	2025-11-25 21:05:01.859291+00	2025-11-25 21:05:31.886354+00
50ed54ba-3f3d-4f05-b937-016aa4a3eed6	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.10819316889405	2025-11-25 20:43:01.127215+00	\N	\N	\N	2025-11-25 20:43:31.144502+00	60.904033476577126	30.017287	{}	2025-11-25 20:43:01.130597+00	2025-11-25 20:43:31.15137+00
fba5a925-70b7-4a61-8195-25081ed311c0	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.53008911759677	2025-11-25 21:57:19.583331+00	\N	\N	\N	2025-11-25 21:57:55.605087+00	61.87171653604463	36.021756	{}	2025-11-25 21:57:19.586417+00	2025-11-25 21:57:55.608169+00
4c4e21e9-4b54-4345-9a94-d6d3412552de	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.08217210287836	2025-11-25 20:44:11.166166+00	\N	\N	\N	2025-11-25 20:44:35.181375+00	65.18474263704883	24.015209	{}	2025-11-25 20:44:11.169202+00	2025-11-25 20:44:35.184418+00
2a9ed847-427e-4a06-904f-a04ed3e424af	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	72.66849737838999	2025-11-25 21:07:07.928359+00	\N	\N	\N	2025-11-25 21:07:37.948237+00	57.3738864725054	30.019878	{}	2025-11-25 21:07:07.931879+00	2025-11-25 21:07:37.951661+00
29c1b6ec-430b-40b0-a794-fc642dee1824	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.27998851945915	2025-11-25 20:45:11.204044+00	\N	\N	\N	2025-11-25 20:45:37.217382+00	63.89894494306313	26.013338	{}	2025-11-25 20:45:11.207091+00	2025-11-25 20:45:37.221243+00
aebb4e43-a983-424e-9750-973ec2a76836	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.618050525685	2025-11-25 21:08:09.969451+00	\N	\N	\N	2025-11-25 21:08:43.985973+00	56.82793701877754	34.016522	{}	2025-11-25 21:08:09.976739+00	2025-11-25 21:08:43.989028+00
43772db9-314d-4e0c-bc51-d8458c4421de	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.06561946438975	2025-11-25 21:58:25.621842+00	\N	\N	\N	2025-11-25 21:58:57.63926+00	57.295692618226354	32.017418	{}	2025-11-25 21:58:25.625091+00	2025-11-25 21:58:57.649098+00
c7278ef0-a287-4f3a-b43e-2432eded611b	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.72471727364191	2025-11-25 21:09:12.000547+00	\N	\N	\N	2025-11-25 21:09:42.014734+00	67.10284867313364	30.014187	{}	2025-11-25 21:09:12.009087+00	2025-11-25 21:09:42.018083+00
19a19dd7-8c8b-4f32-874c-15266740f228	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.51270703402629	2025-11-25 22:59:07.564382+00	\N	\N	\N	2025-11-25 22:59:39.584391+00	61.89451468430206	32.020009	{}	2025-11-25 22:59:07.566868+00	2025-11-25 22:59:39.591305+00
264beea7-9895-47ae-951f-bb55b41a62bf	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.31260623583677	2025-11-25 21:10:20.033352+00	\N	\N	\N	2025-11-25 21:10:52.050961+00	54.56585985627501	32.017609	{}	2025-11-25 21:10:20.039068+00	2025-11-25 21:10:52.054457+00
c880d8cf-22f6-4b2e-aa76-8c566f033dc0	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.71273340341891	2025-11-25 21:59:27.662648+00	\N	\N	\N	2025-11-25 22:00:01.679999+00	55.59769840808653	34.017351	{}	2025-11-25 21:59:27.666008+00	2025-11-25 22:00:01.687107+00
812bab02-33d6-43c5-82db-5e22a5f59561	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.4437699164724	2025-11-25 21:11:18.065013+00	\N	\N	\N	2025-11-25 21:11:46.082067+00	62.98917967253222	28.017054	{}	2025-11-25 21:11:18.068057+00	2025-11-25 21:11:46.08517+00
acd4407d-c173-4e22-aac9-4cdb93be0650	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.80071071279684	2025-11-25 21:14:24.172278+00	\N	\N	\N	2025-11-25 21:14:58.189864+00	57.6627023106156	34.017586	{}	2025-11-25 21:14:24.175467+00	2025-11-25 21:14:58.193427+00
76bbf7a5-5cda-4dac-89db-6fc043cc6e40	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	72.58545431817042	2025-11-25 22:00:31.69514+00	\N	\N	\N	2025-11-25 22:01:03.711848+00	60.21706445487647	32.016708	{}	2025-11-25 22:00:31.698007+00	2025-11-25 22:01:03.71875+00
3b3bb2e0-ac17-46bc-8163-83f073f59f04	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.83800275707277	2025-11-25 21:17:30.270586+00	\N	\N	\N	2025-11-25 21:17:32.272619+00	61.90285166363715	2.002033	{}	2025-11-25 21:17:30.273032+00	2025-11-25 21:17:32.276068+00
45aa60c5-f9a4-49c7-b1d5-d3c0c5c2fa54	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.92149062804711	2025-11-25 23:01:15.632852+00	\N	\N	\N	2025-11-25 23:01:49.650632+00	56.24115127688863	34.01778	{}	2025-11-25 23:01:15.635503+00	2025-11-25 23:01:49.653644+00
bf721fac-e143-4819-ab83-ee287c59b0ad	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.55706961986232	2025-11-25 21:17:38.277499+00	\N	\N	\N	2025-11-25 21:18:00.286669+00	66.84122558933991	22.00917	{}	2025-11-25 21:17:38.280467+00	2025-11-25 21:18:00.290391+00
f1ee203a-a1f9-40d8-a0d3-952b7913650a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.29835712308713	2025-11-25 22:01:31.723628+00	\N	\N	\N	2025-11-25 22:02:01.741045+00	62.957818591221084	30.017417	{}	2025-11-25 22:01:32.732379+00	2025-11-25 22:02:01.748439+00
f34d3942-9850-4905-84fe-9e1a9f41432d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.380897108032	2025-11-25 21:32:14.76491+00	\N	\N	\N	2025-11-25 21:32:46.783672+00	61.10206945415496	32.018762	{}	2025-11-25 21:32:14.76813+00	2025-11-25 21:32:46.786791+00
79a51074-8afc-40ac-841d-8079fce59478	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.25679975988247	2025-11-25 21:33:18.799926+00	\N	\N	\N	2025-11-25 21:33:46.81514+00	60.96494361481127	28.015214	{}	2025-11-25 21:33:18.802831+00	2025-11-25 21:33:46.81837+00
8aeb78fe-d58d-45f9-991e-7a10f2c50a99	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.40551296346409	2025-11-25 22:03:41.796963+00	\N	\N	\N	2025-11-25 22:04:07.811406+00	64.30219285621806	26.014443	{}	2025-11-25 22:03:41.799656+00	2025-11-25 22:04:07.814681+00
00191b3e-9a91-4baf-b0bd-dadefe4f45ee	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.91535283711295	2025-11-25 21:34:22.834132+00	\N	\N	\N	2025-11-25 21:34:46.846042+00	64.75778047469565	24.01191	{}	2025-11-25 21:34:22.837008+00	2025-11-25 21:34:46.848937+00
4fb080b0-8920-49d3-a946-5886ad125dd8	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.11052572606937	2025-11-25 23:02:21.667936+00	\N	\N	\N	2025-11-25 23:02:45.680399+00	63.5527911034619	24.012463	{}	2025-11-25 23:02:21.670799+00	2025-11-25 23:02:45.68333+00
899fbb8e-f67f-44d8-89e4-952ac5d03e74	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.62660413137925	2025-11-25 21:35:26.871196+00	\N	\N	\N	2025-11-25 21:35:54.886898+00	62.823275082558936	28.015702	{}	2025-11-25 21:35:26.878911+00	2025-11-25 21:35:54.896702+00
cf8da801-617a-4ba6-96ce-92ac4d826ae3	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.02906623954063	2025-11-25 22:04:43.830596+00	\N	\N	\N	2025-11-25 22:05:11.844136+00	67.49520502130886	28.01354	{}	2025-11-25 22:04:43.833119+00	2025-11-25 22:05:11.846806+00
2753e56f-6a8d-4efd-a034-cdcfb1867c53	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.1681556729393	2025-11-25 22:05:47.863599+00	\N	\N	\N	2025-11-25 22:06:15.87873+00	61.299180827991314	28.015131	{}	2025-11-25 22:05:47.866777+00	2025-11-25 22:06:15.881571+00
95d64548-bf81-496a-aa35-452c326d5834	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.8738605029932	2025-11-25 23:03:25.699038+00	\N	\N	\N	2025-11-25 23:03:59.715348+00	52.83490202972108	34.01631	{}	2025-11-25 23:03:25.701011+00	2025-11-25 23:03:59.72157+00
95ae0cf5-765c-4864-afff-72020d12aa95	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.31737974070202	2025-11-25 22:07:51.928774+00	\N	\N	\N	2025-11-25 22:08:17.942336+00	66.25733332913832	26.013562	{}	2025-11-25 22:07:51.931333+00	2025-11-25 22:08:17.945032+00
ad145a70-664f-4531-a0bf-138cba21609e	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.64146706031208	2025-11-25 22:08:57.960864+00	\N	\N	\N	2025-11-25 22:09:23.975937+00	65.95735604579629	26.015073	{}	2025-11-25 22:08:57.963382+00	2025-11-25 22:09:23.978681+00
3f1a2663-b6e3-40ac-bd67-a48aed3540b2	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.70919017638604	2025-11-25 23:05:27.760194+00	\N	\N	\N	2025-11-25 23:05:55.77352+00	61.670825695980255	28.013326	{}	2025-11-25 23:05:27.76256+00	2025-11-25 23:05:55.776046+00
c8a11271-c68c-4f2b-9fcb-c803fceab1b4	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.33624114568339	2025-11-25 22:11:04.026872+00	\N	\N	\N	2025-11-25 22:11:32.040667+00	64.68539681377418	28.013795	{}	2025-11-25 22:11:04.034415+00	2025-11-25 22:11:32.047643+00
a5fddb4a-6ccc-47f9-97f6-6ba323255a42	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.47698219076887	2025-11-25 22:13:04.093345+00	\N	\N	\N	2025-11-25 22:13:38.108833+00	60.22053036045269	34.015488	{}	2025-11-25 22:13:04.096228+00	2025-11-25 22:13:38.116828+00
da275b0b-e13c-4d62-8514-87a9edb71b72	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.7879585862207	2025-11-25 23:08:35.857944+00	\N	\N	\N	2025-11-25 23:09:07.872448+00	61.52722930335545	32.014504	{}	2025-11-25 23:08:35.860334+00	2025-11-25 23:09:07.875535+00
ef9f62cd-21db-430c-9321-c005a6702992	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.74978812609953	2025-11-25 22:14:14.127216+00	\N	\N	\N	2025-11-25 22:14:38.139322+00	61.30922778129772	24.012106	{}	2025-11-25 22:14:14.129656+00	2025-11-25 22:14:38.820494+00
df8dba07-2e0d-4f29-b24c-3fcddd24df76	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.77726296161069	2025-11-25 22:31:52.69129+00	\N	\N	\N	2025-11-25 22:32:28.713401+00	62.56414671424823	36.022111	{}	2025-11-25 22:31:52.694226+00	2025-11-25 22:32:28.716261+00
3fa7f4b1-aa2c-4ddd-a977-fb1bcbc4eac8	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.22761233811862	2025-11-25 23:09:35.887235+00	\N	\N	\N	2025-11-25 23:10:11.909207+00	57.34517510107615	36.021972	{}	2025-11-25 23:09:35.89021+00	2025-11-25 23:10:11.916773+00
182eecd5-eadd-44e8-8273-2befde2b4ab8	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.82330547886029	2025-11-25 22:33:26.750525+00	\N	\N	\N	2025-11-25 22:33:28.75218+00	67.47380557947923	2.001655	{}	2025-11-25 22:33:26.753126+00	2025-11-25 22:33:28.755132+00
af1373d3-9ab8-4d5e-afb3-efee6bd9a3e1	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.33513254116983	2025-11-25 22:32:56.730244+00	\N	\N	\N	2025-11-25 22:33:30.753871+00	62.37182523188978	34.023627	{}	2025-11-25 22:32:56.732433+00	2025-11-25 22:33:30.75631+00
bf972b23-39b2-46b4-b510-70ba6a750003	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.88938954163861	2025-11-25 23:12:43.986259+00	\N	\N	\N	2025-11-25 23:13:22.00728+00	60.8769059483369	38.021021	{}	2025-11-25 23:12:43.989147+00	2025-11-25 23:13:22.010303+00
891cabad-b86d-44f1-91b5-aa9296a219b6	968bfc86-180d-454f-8417-09f433813918	ACTIVE	74.89925295819468	2025-11-25 20:23:11.200642+00	\N	\N	\N	\N	\N	\N	{}	2025-11-25 20:23:11.207962+00	2025-11-25 20:23:11.207962+00
90fdfd24-72bd-4879-8589-f9c003c9aeea	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	82.38185063077422	2025-11-25 19:42:16.602644+00	\N	\N	\N	2025-11-25 19:42:22.608297+00	77.5324778683495	6.005653	{}	2025-11-25 19:42:16.61235+00	2025-11-25 19:42:22.617836+00
125cf436-9974-498c-8879-081e4ff7149d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	82.18152540078722	2025-11-25 19:44:28.716982+00	\N	\N	\N	2025-11-25 19:44:30.723186+00	76.67536181537977	2.006204	{}	2025-11-25 19:44:28.726261+00	2025-11-25 19:44:30.731489+00
b1756649-5258-466b-a551-a12be8df461f	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.89791540779352	2025-11-25 20:31:28.747699+00	\N	\N	\N	2025-11-25 20:32:04.767571+00	61.704255555820396	36.019872	{}	2025-11-25 20:31:28.751669+00	2025-11-25 20:32:04.771737+00
379dbd54-951d-4045-b23f-2fc59def0e3b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	78.0939970093451	2025-11-25 19:45:20.769935+00	\N	\N	\N	2025-11-25 19:45:36.785422+00	68.68158463045522	16.015487	{}	2025-11-25 19:45:20.778699+00	2025-11-25 19:45:36.800004+00
4bc1ac6c-0ba6-4ce4-9641-7c5b5826c6ff	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.22292389716567	2025-11-25 21:02:59.790321+00	\N	\N	\N	2025-11-25 21:03:25.803917+00	59.59866338226458	26.013596	{}	2025-11-25 21:02:59.795371+00	2025-11-25 21:03:25.806952+00
4d8a98f3-692e-40e5-a38d-5cfc51a61bdd	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	75.44422286762908	2025-11-25 19:47:20.876215+00	\N	\N	\N	2025-11-25 19:47:50.899839+00	60.36239697512332	30.023624	{}	2025-11-25 19:47:20.886889+00	2025-11-25 19:47:50.920804+00
673dbe69-0f6c-49ad-83b6-9b9a48367a2e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.24590296416774	2025-11-25 20:32:34.783303+00	\N	\N	\N	2025-11-25 20:33:04.801261+00	59.097276004265	30.017958	{}	2025-11-25 20:32:34.787162+00	2025-11-25 20:33:04.804655+00
38827225-6bf8-41d7-beb1-d3dfb8b2eaef	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.88337296234032	2025-11-25 19:49:26.970396+00	\N	\N	\N	2025-11-25 19:49:55.005299+00	65.8536812904511	28.034903	{}	2025-11-25 19:49:26.982345+00	2025-11-25 19:49:55.01029+00
ba2515b7-dcab-4d1d-95e0-3c42fb2efbe7	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.1363780818568	2025-11-25 21:56:21.554091+00	\N	\N	\N	2025-11-25 21:56:55.570865+00	54.08286481583981	34.016774	{}	2025-11-25 21:56:21.56268+00	2025-11-25 21:56:55.573502+00
f7ac66f0-a640-453c-81b3-5cfdf311b0f4	968bfc86-180d-454f-8417-09f433813918	CLEARED	79.24532527189905	2025-11-25 19:50:37.038371+00	\N	\N	\N	2025-11-25 19:50:53.052055+00	64.06892510693119	16.013684	{}	2025-11-25 19:50:37.045449+00	2025-11-25 19:50:53.074829+00
09c34152-55c6-44f4-86c8-1eaed26f8897	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.59095619468384	2025-11-25 20:33:38.818786+00	\N	\N	\N	2025-11-25 20:34:02.831688+00	64.69537545703821	24.012902	{}	2025-11-25 20:33:38.824841+00	2025-11-25 20:34:02.835394+00
0207c699-90b7-4af0-93e9-1e31e4e274e3	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.10884336093385	2025-11-25 19:51:29.095461+00	\N	\N	\N	2025-11-25 19:52:01.125634+00	60.428226817922734	32.030173	{}	2025-11-25 19:51:29.105081+00	2025-11-25 19:52:01.130165+00
59490b0d-34e0-42db-b9a4-39618c86c9ca	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.10833062957386	2025-11-25 21:04:01.824707+00	\N	\N	\N	2025-11-25 21:04:25.837706+00	65.26827913291324	24.012999	{}	2025-11-25 21:04:01.828067+00	2025-11-25 21:04:25.840596+00
21849d7b-04d1-4011-b634-5fbbc8942f4c	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.99790945234885	2025-11-25 19:54:35.254038+00	\N	\N	\N	2025-11-25 19:55:09.284425+00	62.3181757180033	34.030387	{}	2025-11-25 19:54:35.261002+00	2025-11-25 19:55:09.292992+00
812c66c8-3c89-40a2-9798-293cba67e742	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.92203820390013	2025-11-25 20:34:42.854506+00	\N	\N	\N	2025-11-25 20:35:08.866694+00	63.556730607697936	26.012188	{}	2025-11-25 20:34:42.857722+00	2025-11-25 20:35:08.872283+00
5fd06165-f40f-4790-a64b-1dc58209c9b5	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.85776785892388	2025-11-25 22:58:09.534683+00	\N	\N	\N	2025-11-25 22:58:33.547817+00	67.57786662200738	24.013134	{}	2025-11-25 22:58:09.537587+00	2025-11-25 22:58:33.550115+00
157a539c-5747-4d3b-91bd-fb188fdb8ec4	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.53587704444408	2025-11-25 20:35:44.887764+00	\N	\N	\N	2025-11-25 20:36:10.898924+00	64.11856374762081	26.01116	{}	2025-11-25 20:35:44.891012+00	2025-11-25 20:36:10.902425+00
4f74fa5b-bc95-49ce-a77c-343e6de2a5de	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.22055358870944	2025-11-25 21:05:03.859374+00	\N	\N	\N	2025-11-25 21:05:31.877457+00	66.42158550489326	28.018083	{}	2025-11-25 21:05:03.862103+00	2025-11-25 21:05:31.881252+00
2147e0b9-1c41-4fc3-8c73-c9a3cc35ee8d	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.88711843178083	2025-11-25 20:36:44.915854+00	\N	\N	\N	2025-11-25 20:37:16.93173+00	57.817291730658866	32.015876	{}	2025-11-25 20:36:44.919719+00	2025-11-25 20:37:16.93589+00
ea0a1e41-cf71-45ee-9ea3-d181358c2f78	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.91074668063506	2025-11-25 21:58:27.624418+00	\N	\N	\N	2025-11-25 21:58:53.636145+00	63.1714942065426	26.011727	{}	2025-11-25 21:58:27.627445+00	2025-11-25 21:58:53.639546+00
bb4b6233-a8a6-4ce1-9644-f03bbbf7a8f2	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.53537309340797	2025-11-25 20:40:59.058808+00	\N	\N	\N	2025-11-25 20:41:23.072878+00	67.94111899650551	24.01407	{}	2025-11-25 20:40:59.062551+00	2025-11-25 20:41:23.076242+00
6306a315-9dd0-49cf-a845-dad47497e55e	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.03091419998927	2025-11-25 21:06:07.898883+00	\N	\N	\N	2025-11-25 21:06:35.912377+00	66.0574014605646	28.013494	{}	2025-11-25 21:06:07.903802+00	2025-11-25 21:06:35.916186+00
4e3ddd7f-d39b-45ef-938d-f5a5d18967e6	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.16972825895621	2025-11-25 21:07:09.930758+00	\N	\N	\N	2025-11-25 21:07:33.943988+00	66.66766759813838	24.01323	{}	2025-11-25 21:07:09.933796+00	2025-11-25 21:07:33.947231+00
b14c5fe1-501d-44b5-b556-1a43e9c809e5	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.25064774249664	2025-11-25 21:59:29.664704+00	\N	\N	\N	2025-11-25 22:00:01.679934+00	57.229539348589284	32.01523	{}	2025-11-25 21:59:29.667965+00	2025-11-25 22:00:01.682512+00
e6516800-6c56-4187-9f1c-401f4fe6cda1	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.57055666039209	2025-11-25 21:11:22.068243+00	\N	\N	\N	2025-11-25 21:11:44.080311+00	67.00672590907196	22.012068	{}	2025-11-25 21:11:22.07245+00	2025-11-25 21:11:44.089335+00
b5e6fc4a-ccb9-4a6b-8134-f4921ee0638f	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.50867815514283	2025-11-25 22:59:11.567517+00	\N	\N	\N	2025-11-25 22:59:39.584315+00	64.53193017241907	28.016798	{}	2025-11-25 22:59:11.570694+00	2025-11-25 22:59:39.58662+00
ad4ee061-1580-4613-967a-b7cbf54ed01e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.47357866357822	2025-11-25 21:11:48.083868+00	\N	\N	\N	2025-11-25 21:11:50.085931+00	57.95242001623474	2.002063	{}	2025-11-25 21:11:48.508982+00	2025-11-25 21:11:50.088969+00
4791e8ab-b69c-4eb6-9a32-f87a38816e98	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.61532808568145	2025-11-25 22:00:35.697832+00	\N	\N	\N	2025-11-25 22:01:03.711768+00	63.34981690099403	28.013936	{}	2025-11-25 22:00:35.700267+00	2025-11-25 22:01:03.71446+00
c190cf7b-3505-46c9-a495-636aac7836b8	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.78424596343653	2025-11-25 21:12:20.099926+00	\N	\N	\N	2025-11-25 21:12:58.121515+00	56.478919987153716	38.021589	{}	2025-11-25 21:12:20.597101+00	2025-11-25 21:12:58.124554+00
d079f9a1-4473-4a71-80d1-8937d6a52121	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.22137760840654	2025-11-25 21:13:22.134708+00	\N	\N	\N	2025-11-25 21:13:52.15071+00	65.51274536988942	30.016002	{}	2025-11-25 21:13:22.137909+00	2025-11-25 21:13:52.153942+00
560eb211-f842-405e-9c6f-f6218f879eab	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.27113201527975	2025-11-25 22:01:33.725246+00	\N	\N	\N	2025-11-25 22:02:01.740983+00	62.228129221245894	28.015737	{}	2025-11-25 22:01:33.728038+00	2025-11-25 22:02:01.74351+00
400471cc-9f2d-49fd-8947-a33e1adc4f5d	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.35101012967037	2025-11-25 21:15:32.205049+00	\N	\N	\N	2025-11-25 21:16:02.219522+00	62.199088668258455	30.014473	{}	2025-11-25 21:15:33.086767+00	2025-11-25 21:16:02.222554+00
ebbf9a12-264a-4d9c-8a57-cfa0513ab274	968bfc86-180d-454f-8417-09f433813918	CLEARED	81.87305041677895	2025-11-25 23:00:23.60545+00	\N	\N	\N	2025-11-25 23:00:49.619214+00	56.0353533537768	26.013764	{}	2025-11-25 23:00:23.608385+00	2025-11-25 23:00:49.622406+00
a98a298b-0590-4b84-acc2-f55853bc9c21	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.47744699266997	2025-11-25 21:16:32.235863+00	\N	\N	\N	2025-11-25 21:17:04.25389+00	61.608010200660004	32.018027	{}	2025-11-25 21:16:32.239123+00	2025-11-25 21:17:04.257077+00
fd902a37-c5a5-4428-9a54-5dae2d17456d	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.1506460784787	2025-11-25 22:02:39.76256+00	\N	\N	\N	2025-11-25 22:03:03.775323+00	64.99604163384696	24.012763	{}	2025-11-25 22:02:39.766352+00	2025-11-25 22:03:03.778605+00
52bcfb5f-cf84-4bf9-b61a-4f23842748b3	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.80395043370669	2025-11-25 21:35:26.871119+00	\N	\N	\N	2025-11-25 21:35:54.886847+00	59.37642105125666	28.015728	{}	2025-11-25 21:35:26.8739+00	2025-11-25 21:35:54.890397+00
8eb91310-e6ea-495b-bffc-c1e27a8d517e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.13871047379425	2025-11-25 22:05:47.863697+00	\N	\N	\N	2025-11-25 22:06:15.8788+00	60.45528787089016	28.015103	{}	2025-11-25 22:05:47.87175+00	2025-11-25 22:06:15.884304+00
949b4248-d77c-4140-9258-27a3198ffefb	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.92524816768072	2025-11-25 23:06:35.793506+00	\N	\N	\N	2025-11-25 23:06:57.803546+00	65.8455556916584	22.01004	{}	2025-11-25 23:06:35.796156+00	2025-11-25 23:06:57.805662+00
ca1c9a92-3792-40f5-8c3b-5edee32d627e	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.14769636164014	2025-11-25 22:06:53.898006+00	\N	\N	\N	2025-11-25 22:07:17.909494+00	64.79498020578154	24.011488	{}	2025-11-25 22:06:53.900679+00	2025-11-25 22:07:17.912274+00
ac1a594c-ec41-4481-9053-92a0d52ed9c5	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.78369193488017	2025-11-25 22:13:10.096408+00	\N	\N	\N	2025-11-25 22:13:38.108776+00	60.70762728911905	28.012368	{}	2025-11-25 22:13:10.099175+00	2025-11-25 22:13:38.111853+00
816184f2-5f47-442c-aa76-3b1cc3f76288	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	72.27426730645841	2025-11-25 23:07:33.825275+00	\N	\N	\N	2025-11-25 23:08:01.841522+00	60.85818452695879	28.016247	{}	2025-11-25 23:07:33.832095+00	2025-11-25 23:08:01.844458+00
f401879c-ce70-4a49-a1e8-652c690ec912	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.6828644828698	2025-11-25 22:15:18.159077+00	\N	\N	\N	2025-11-25 22:15:36.167645+00	67.58058577689671	18.008568	{}	2025-11-25 22:15:18.16198+00	2025-11-25 22:15:36.170116+00
96bf04ec-27c0-4592-b3e3-07ad5d9db24d	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.90426314127029	2025-11-25 22:35:04.801352+00	\N	\N	\N	2025-11-25 22:35:34.814467+00	62.615677815427624	30.013115	{}	2025-11-25 22:35:04.804647+00	2025-11-25 22:35:34.817058+00
6afdb314-ae71-44cf-b35a-f4bc37041f4c	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	73.2274020043309	2025-11-25 23:10:41.925456+00	\N	\N	\N	2025-11-25 23:11:09.938956+00	62.09865080928612	28.0135	{}	2025-11-25 23:10:41.928276+00	2025-11-25 23:11:09.946016+00
7565a1fd-5ffd-4ffd-955e-7a1932e188d5	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.40394833852797	2025-11-25 22:36:08.830651+00	\N	\N	\N	2025-11-25 22:36:36.844433+00	67.8020777499168	28.013782	{}	2025-11-25 22:36:08.833159+00	2025-11-25 22:36:36.847651+00
686239f7-d367-47d1-95d4-0197255cfa2b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.73763255669986	2025-11-25 22:37:06.861949+00	\N	\N	\N	2025-11-25 22:37:40.88131+00	60.10939559088004	34.019361	{}	2025-11-25 22:37:06.865044+00	2025-11-25 22:37:40.883338+00
bfbae808-00d4-441f-a3ae-b3bb88dfa978	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	73.62697720520357	2025-11-25 23:11:45.955346+00	\N	\N	\N	2025-11-25 23:12:15.970191+00	59.21831846290824	30.014845	{}	2025-11-25 23:11:45.958136+00	2025-11-25 23:12:15.977326+00
f9b7ef06-e1fb-4ba6-b15a-8b283f6470e9	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.83874680037331	2025-11-25 22:41:23.004991+00	\N	\N	\N	2025-11-25 22:41:47.016809+00	67.29670269779663	24.011818	{}	2025-11-25 22:41:23.646316+00	2025-11-25 22:41:47.019782+00
1105cb5c-2ab2-49fc-82e0-680f0616173d	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.85792394916209	2025-11-25 22:42:27.037443+00	\N	\N	\N	2025-11-25 22:43:03.055418+00	52.194863907963054	36.017975	{}	2025-11-25 22:42:27.763262+00	2025-11-25 22:43:03.057849+00
552fdd12-de98-4ae0-b60d-3d47358b1b3d	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.10098755459883	2025-11-25 23:12:47.989981+00	\N	\N	\N	2025-11-25 23:13:16.003839+00	64.03229737227255	28.013858	{}	2025-11-25 23:12:47.993044+00	2025-11-25 23:13:16.006778+00
1454682b-d35d-4713-b499-56104dfa329b	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.75735695340417	2025-11-25 23:13:52.022788+00	\N	\N	\N	2025-11-25 23:14:18.036191+00	62.482065447431225	26.013403	{}	2025-11-25 23:13:52.025118+00	2025-11-25 23:14:18.039056+00
e5d3934c-088f-4718-ae04-c098acf3c962	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.9836904844677	2025-11-25 23:14:56.055205+00	\N	\N	\N	2025-11-25 23:15:18.066851+00	67.75968218899642	22.011646	{}	2025-11-25 23:14:56.058158+00	2025-11-25 23:15:18.069353+00
214cd69d-9dfb-4138-90dc-dfd031590c44	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.70153382421961	2025-11-25 23:15:58.088734+00	\N	\N	\N	2025-11-25 23:16:24.103046+00	67.43911875469657	26.014312	{}	2025-11-25 23:15:58.091749+00	2025-11-25 23:16:24.105887+00
4c8972cb-2c31-4ddf-8326-1756bb75b593	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.70607293626621	2025-11-25 23:18:00.15976+00	\N	\N	\N	2025-11-25 23:18:32.176241+00	59.44245919897392	32.016481	{}	2025-11-25 23:18:00.162011+00	2025-11-25 23:18:32.183822+00
519c2c14-836c-48e1-8d9c-e52dd74ddf1f	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.08898986000159	2025-11-25 23:19:32.210325+00	\N	\N	\N	2025-11-25 23:19:36.213402+00	59.130123425929604	4.003077	{}	2025-11-25 23:19:32.213004+00	2025-11-25 23:19:36.216511+00
a1a0be02-3358-47e9-81e4-497e9fe64da7	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.92334824071742	2025-11-25 23:19:02.190823+00	\N	\N	\N	2025-11-25 23:19:36.213508+00	60.42937929301154	34.022685	{}	2025-11-25 23:19:02.193652+00	2025-11-25 23:19:36.221651+00
ae1b1b8d-8981-45b3-9fff-21eb1d2382fb	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.7847578829735	2025-11-25 19:43:10.651193+00	\N	\N	\N	2025-11-25 19:43:36.672223+00	66.84069562552656	26.02103	{}	2025-11-25 19:43:10.656199+00	2025-11-25 19:43:36.678793+00
ff66f345-5d11-486d-bacd-af5c8a815642	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.62452612414677	2025-11-25 20:33:34.81644+00	\N	\N	\N	2025-11-25 20:34:10.836535+00	58.10135792557113	36.020095	{}	2025-11-25 20:33:34.820055+00	2025-11-25 20:34:10.840556+00
ab20d22c-9266-46a3-87f4-615c3c917a30	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	82.56573694995127	2025-11-25 19:44:18.704249+00	\N	\N	\N	2025-11-25 19:44:26.713166+00	74.51601362316055	8.008917	{}	2025-11-25 19:44:18.711619+00	2025-11-25 19:44:26.719524+00
935e0006-434a-4769-bb0c-1763bc71b292	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.42071174667319	2025-11-25 21:03:55.820563+00	\N	\N	\N	2025-11-25 21:04:27.83992+00	60.70888904922093	32.019357	{}	2025-11-25 21:03:55.824914+00	2025-11-25 21:04:27.843063+00
a9cbbd0f-acb8-46e0-b5f9-8839df627910	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.41597008755285	2025-11-25 19:46:20.826576+00	\N	\N	\N	2025-11-25 19:46:44.850274+00	65.61838291289999	24.023698	{}	2025-11-25 19:46:20.835693+00	2025-11-25 19:46:44.860269+00
88cde45b-aad1-4fbc-b753-71313548d78e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.314649591126	2025-11-25 20:34:36.850289+00	\N	\N	\N	2025-11-25 20:35:10.870142+00	57.66925375801447	34.019853	{}	2025-11-25 20:34:37.803643+00	2025-11-25 20:35:10.874282+00
e1ce3bc1-c1aa-47a9-a958-47763e6d0cfe	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.76228977278672	2025-11-25 19:51:33.102769+00	\N	\N	\N	2025-11-25 19:51:57.121378+00	65.36270170593096	24.018609	{}	2025-11-25 19:51:33.109868+00	2025-11-25 19:51:57.125603+00
03a6f67f-aa59-4549-89e6-8fe53be50e24	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.32201627233492	2025-11-25 21:57:27.586718+00	\N	\N	\N	2025-11-25 21:57:53.60274+00	59.88377397261001	26.016022	{}	2025-11-25 21:57:27.590151+00	2025-11-25 21:57:53.605631+00
9912b962-4f49-436c-bc4e-2a500976c86f	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.29991110766602	2025-11-25 19:54:37.258293+00	\N	\N	\N	2025-11-25 19:55:03.279199+00	67.99100100154482	26.020906	{}	2025-11-25 19:54:37.266654+00	2025-11-25 19:55:03.283738+00
380a725e-c912-4829-a5a9-e7ebfe84772b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	73.03254120214902	2025-11-25 20:35:42.885343+00	\N	\N	\N	2025-11-25 20:36:12.900759+00	62.69340142057206	30.015416	{}	2025-11-25 20:35:42.888593+00	2025-11-25 20:36:12.90444+00
d9edb7ed-56f2-4818-b665-1c503be46162	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.52226570680445	2025-11-25 21:05:59.892524+00	\N	\N	\N	2025-11-25 21:06:35.912495+00	62.14538724449292	36.019971	{}	2025-11-25 21:05:59.897926+00	2025-11-25 21:06:35.921327+00
26f55846-71fd-4fce-803b-4b5359c618f3	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.19385782031182	2025-11-25 20:36:42.913063+00	\N	\N	\N	2025-11-25 20:37:14.928846+00	61.53904029115588	32.015783	{}	2025-11-25 20:36:42.917854+00	2025-11-25 20:37:14.934597+00
b8e7b0b8-84ef-4b3b-8371-008df91a8ed7	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.82967969365299	2025-11-25 23:00:13.600096+00	\N	\N	\N	2025-11-25 23:00:49.619313+00	50.525678429242504	36.019217	{}	2025-11-25 23:00:13.602399+00	2025-11-25 23:00:49.627404+00
c5858954-ad31-491f-b72e-6a6fbf66b885	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.23864781022219	2025-11-25 20:37:48.951368+00	\N	\N	\N	2025-11-25 20:38:12.965019+00	66.40402336034686	24.013651	{}	2025-11-25 20:37:48.957712+00	2025-11-25 20:38:12.968088+00
f2fa0003-adec-474e-b21b-35ed3d4bc2e4	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.12810191551063	2025-11-25 21:08:09.969365+00	\N	\N	\N	2025-11-25 21:08:39.982766+00	67.75267693331884	30.013401	{}	2025-11-25 21:08:09.972026+00	2025-11-25 21:08:39.985701+00
a1fb5a8e-2df6-41a0-a09a-31404d2dd4bb	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.89401618593386	2025-11-25 20:38:52.987215+00	\N	\N	\N	2025-11-25 20:39:21.00138+00	63.67669636991726	28.014165	{}	2025-11-25 20:38:52.990699+00	2025-11-25 20:39:21.005528+00
d9eff3b1-da08-410b-883c-e184549879a6	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.23518630795486	2025-11-25 22:07:45.923687+00	\N	\N	\N	2025-11-25 22:08:21.944496+00	57.91015410152069	36.020809	{}	2025-11-25 22:07:45.92672+00	2025-11-25 22:08:21.947267+00
0d1baebd-63f2-4764-9129-b7c1685d9971	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.34395115216164	2025-11-25 20:39:57.023495+00	\N	\N	\N	2025-11-25 20:40:21.037284+00	63.58027630954641	24.013789	{}	2025-11-25 20:39:57.027345+00	2025-11-25 20:40:21.040346+00
bdbcf6cb-3abf-44ff-8123-7af4fc05eced	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.29738560004965	2025-11-25 21:09:12.000626+00	\N	\N	\N	2025-11-25 21:09:48.018177+00	53.42479216846796	36.017551	{}	2025-11-25 21:09:12.003877+00	2025-11-25 21:09:48.021304+00
dc1b86b7-7da4-4de1-842c-16ba2866b34d	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.70893198333448	2025-11-25 20:42:01.093844+00	\N	\N	\N	2025-11-25 20:42:27.108058+00	65.58275685411004	26.014214	{}	2025-11-25 20:42:01.096993+00	2025-11-25 20:42:27.111531+00
502cdf55-a5a7-4722-9064-36e0def16443	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.51934433654165	2025-11-25 20:43:05.130302+00	\N	\N	\N	2025-11-25 20:43:31.144442+00	64.36266529803484	26.01414	{}	2025-11-25 20:43:05.133915+00	2025-11-25 20:43:31.147686+00
a2e79d40-f8d4-482e-9d9a-9e74e69ba829	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.98995569141424	2025-11-25 21:10:20.033234+00	\N	\N	\N	2025-11-25 21:10:44.045961+00	62.79807199458733	24.012727	{}	2025-11-25 21:10:20.036547+00	2025-11-25 21:10:44.248878+00
40062347-7750-461b-bd83-56dfa1c7ee5d	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.82014447762572	2025-11-25 20:46:13.238052+00	\N	\N	\N	2025-11-25 20:46:35.250211+00	66.95364689136727	22.012159	{}	2025-11-25 20:46:13.259716+00	2025-11-25 20:46:35.254301+00
6c131245-2db2-44b4-affa-e8a9b0f46427	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.60245825120005	2025-11-25 22:09:53.991918+00	\N	\N	\N	2025-11-25 22:10:26.009485+00	61.69924958567555	32.017567	{}	2025-11-25 22:09:53.9949+00	2025-11-25 22:10:26.014892+00
ba25046f-417c-46ca-b64a-33099173f95a	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.97265868470478	2025-11-25 21:16:38.239828+00	\N	\N	\N	2025-11-25 21:17:02.251777+00	62.78882926127413	24.011949	{}	2025-11-25 21:16:38.243036+00	2025-11-25 21:17:02.446345+00
4fa81eda-9d6f-48c0-96df-0d6dd4019bc9	968bfc86-180d-454f-8417-09f433813918	CLEARED	82.27320027110268	2025-11-25 23:01:35.642841+00	\N	\N	\N	2025-11-25 23:01:49.650531+00	56.533207313891495	14.00769	{}	2025-11-25 23:01:35.645874+00	2025-11-25 23:01:49.656966+00
45690039-11cd-412f-b3c1-fe379b8a21d4	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.99486759950719	2025-11-25 21:17:36.275673+00	\N	\N	\N	2025-11-25 21:18:04.289523+00	60.92789667024703	28.01385	{}	2025-11-25 21:17:36.278769+00	2025-11-25 21:18:04.292328+00
0317597c-72b2-4d79-898e-258d30b7c299	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.53906018755814	2025-11-25 22:12:00.05533+00	\N	\N	\N	2025-11-25 22:12:36.076532+00	61.95804438384372	36.021202	{}	2025-11-25 22:12:00.058349+00	2025-11-25 22:12:36.078814+00
70f956a8-705c-4308-89f6-302cf33111f6	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.61833012146442	2025-11-25 21:36:24.90444+00	\N	\N	\N	2025-11-25 21:36:26.905768+00	67.12154453787366	2.001328	{}	2025-11-25 21:36:24.907225+00	2025-11-25 21:36:26.908997+00
89008492-3d01-4098-8e2b-e7ed5f583cbf	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.1418811217809	2025-11-25 21:41:09.058818+00	\N	\N	\N	2025-11-25 21:41:13.061753+00	59.14085739681485	4.002935	{}	2025-11-25 21:41:09.061575+00	2025-11-25 21:41:13.177169+00
4350d1df-c288-440a-96fb-2e5b09561836	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.20948436140027	2025-11-25 22:13:00.089777+00	\N	\N	\N	2025-11-25 22:13:02.091425+00	60.157949281285795	2.001648	{}	2025-11-25 22:13:00.092682+00	2025-11-25 22:13:02.640765+00
db3a9334-b1da-4f08-99f4-a62560326e86	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.72656225884916	2025-11-25 21:41:39.078715+00	\N	\N	\N	2025-11-25 21:42:13.093133+00	58.507667933069136	34.014418	{}	2025-11-25 21:41:39.08144+00	2025-11-25 21:42:13.095898+00
6e325491-77fc-4a4b-9696-8303ed1b1c98	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.2908831337622	2025-11-25 23:02:17.664575+00	\N	\N	\N	2025-11-25 23:02:47.682705+00	62.73179354724205	30.01813	{}	2025-11-25 23:02:17.667488+00	2025-11-25 23:02:47.685549+00
3cea68ce-f5df-445c-b6e6-0e81929b3e16	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.21033646141352	2025-11-25 22:35:04.801415+00	\N	\N	\N	2025-11-25 22:35:38.816665+00	62.107028901670276	34.01525	{}	2025-11-25 22:35:04.810005+00	2025-11-25 22:35:38.819187+00
ac945076-92e4-4055-a7cd-ceca3b010a9d	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.15172201952207	2025-11-25 21:44:15.159016+00	\N	\N	\N	2025-11-25 21:44:19.1623+00	60.59108361838482	4.003284	{}	2025-11-25 21:44:15.161551+00	2025-11-25 21:44:19.165261+00
ca5f24e5-7f15-4789-af69-cebc06ce37cd	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	72.0395860268422	2025-11-25 21:43:47.142121+00	\N	\N	\N	2025-11-25 21:44:19.162356+00	58.207691000687134	32.020235	{}	2025-11-25 21:43:47.145186+00	2025-11-25 21:44:19.169963+00
253aae5b-572e-4021-b0e2-5a3daacd8d8f	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.51690358028675	2025-11-25 22:36:08.830711+00	\N	\N	\N	2025-11-25 22:36:42.848334+00	55.22461510811235	34.017623	{}	2025-11-25 22:36:08.839052+00	2025-11-25 22:36:42.850623+00
2b2180dc-9712-4100-9d44-c8a2f4b37b37	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.29881459911319	2025-11-25 23:03:17.694775+00	\N	\N	\N	2025-11-25 23:03:59.715416+00	49.80827797854819	42.020641	{}	2025-11-25 23:03:17.697028+00	2025-11-25 23:03:59.718371+00
d271fcbd-70bc-465d-9e0b-87fab47c2b67	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.29475687868702	2025-11-25 22:37:16.867272+00	\N	\N	\N	2025-11-25 22:37:36.877471+00	67.45090915542141	20.010199	{}	2025-11-25 22:37:16.869975+00	2025-11-25 22:37:36.880262+00
65eb9c05-df6b-4314-abe5-853b50ce27e6	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.67736443377429	2025-11-25 22:38:12.900441+00	\N	\N	\N	2025-11-25 22:38:48.918502+00	55.32992157552849	36.018061	{}	2025-11-25 22:38:12.903534+00	2025-11-25 22:38:48.921501+00
61075f04-324a-486a-8284-cc7469ad1811	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.06674356745489	2025-11-25 23:04:27.728444+00	\N	\N	\N	2025-11-25 23:04:51.739809+00	64.42673925744859	24.011365	{}	2025-11-25 23:04:27.731275+00	2025-11-25 23:04:51.742535+00
8a406e61-8932-40c3-ac6c-51b48ba03134	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.89283921313334	2025-11-25 22:39:12.930948+00	\N	\N	\N	2025-11-25 22:39:44.953418+00	61.527220681724565	32.02247	{}	2025-11-25 22:39:12.933785+00	2025-11-25 22:39:44.956069+00
3505df15-9e71-459f-a72b-c2bf111577fc	968bfc86-180d-454f-8417-09f433813918	CLEARED	79.01790226636285	2025-11-25 22:43:43.078213+00	\N	\N	\N	2025-11-25 22:43:59.085422+00	66.32813758789018	16.007209	{}	2025-11-25 22:43:43.081678+00	2025-11-25 22:43:59.094407+00
021c2efd-ae7b-48a0-9e23-21814bffb081	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.51607155082247	2025-11-25 23:05:23.757877+00	\N	\N	\N	2025-11-25 23:06:01.777668+00	56.57903882228893	38.019791	{}	2025-11-25 23:05:23.759896+00	2025-11-25 23:06:01.780231+00
80fe05ac-25db-46db-a295-f3fac45ba09a	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.00851655778503	2025-11-25 23:07:31.822881+00	\N	\N	\N	2025-11-25 23:07:33.825201+00	67.38386722683055	2.00232	{}	2025-11-25 23:07:31.825246+00	2025-11-25 23:07:33.827391+00
87d054f6-8751-4808-a4b8-942ea41a6155	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.71163309158727	2025-11-25 23:07:35.82728+00	\N	\N	\N	2025-11-25 23:08:01.841443+00	65.43209164834268	26.014163	{}	2025-11-25 23:07:35.856609+00	2025-11-25 23:08:01.849364+00
2d185e5e-e99e-4000-a84e-d7ee53bf888c	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.47065848671498	2025-11-25 23:08:39.860833+00	\N	\N	\N	2025-11-25 23:09:05.870646+00	60.00814356660376	26.009813	{}	2025-11-25 23:08:40.064969+00	2025-11-25 23:09:05.873423+00
1f965864-a340-4c4b-8595-40d2c570c4ec	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.48952520032122	2025-11-25 23:09:41.89237+00	\N	\N	\N	2025-11-25 23:10:11.909127+00	64.48864913745487	30.016757	{}	2025-11-25 23:09:41.895133+00	2025-11-25 23:10:11.911571+00
4b33a398-dedb-4d8e-9208-4b1d70b96efc	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.14340028777977	2025-11-25 23:10:43.927006+00	\N	\N	\N	2025-11-25 23:11:09.938884+00	67.79871397295022	26.011878	{}	2025-11-25 23:10:43.929264+00	2025-11-25 23:11:09.941375+00
67d2d7f3-7cbb-42c3-9de3-05249ecf8d23	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.74361018398181	2025-11-25 23:11:49.957788+00	\N	\N	\N	2025-11-25 23:12:15.97012+00	63.97168227046443	26.012332	{}	2025-11-25 23:11:49.960054+00	2025-11-25 23:12:15.97264+00
b9a210ec-71ae-4f41-a021-38933ed2cfe7	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.36661635341261	2025-11-25 23:17:00.125243+00	\N	\N	\N	2025-11-25 23:17:26.140007+00	62.50278694363542	26.014764	{}	2025-11-25 23:17:00.127832+00	2025-11-25 23:17:26.143122+00
46c40610-c697-4c8b-a751-4b65744eb7be	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.41618156643314	2025-11-25 19:45:14.762449+00	\N	\N	\N	2025-11-25 19:45:40.79271+00	61.839448610502075	26.030261	{}	2025-11-25 19:45:14.770431+00	2025-11-25 19:45:40.80368+00
cce654a1-efd3-4952-89d5-a9e572759fbf	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.43557520088797	2025-11-25 20:47:11.269333+00	\N	\N	\N	2025-11-25 20:47:45.289009+00	55.85347326947228	34.019676	{}	2025-11-25 20:47:11.272379+00	2025-11-25 20:47:45.292299+00
b68f1521-c764-407c-b61c-05bebafb20ed	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.64200810172171	2025-11-25 19:47:20.876104+00	\N	\N	\N	2025-11-25 19:47:50.899637+00	62.81042358614414	30.023533	{}	2025-11-25 19:47:20.880766+00	2025-11-25 19:47:50.907837+00
bd9c979f-1b9a-4848-9509-c4ebe0f7850d	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.1947820865111	2025-11-25 21:12:24.102843+00	\N	\N	\N	2025-11-25 21:12:46.114305+00	67.60392195954813	22.011462	{}	2025-11-25 21:12:24.105683+00	2025-11-25 21:12:46.11787+00
407f30e8-3449-447e-a303-1204f57cdb7d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	75.90369841831865	2025-11-25 19:48:26.926241+00	\N	\N	\N	2025-11-25 19:48:46.941679+00	70.44916910654486	20.015438	{}	2025-11-25 19:48:26.93605+00	2025-11-25 19:48:46.95525+00
ab78c966-7191-4519-b943-1f031154b40e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.51312183042552	2025-11-25 20:48:15.302222+00	\N	\N	\N	2025-11-25 20:48:47.319121+00	60.259165236427044	32.016899	{}	2025-11-25 20:48:15.30579+00	2025-11-25 20:48:47.322141+00
50419f0d-e110-420f-904a-ef1bab9b1f10	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	76.89152008339225	2025-11-25 19:50:33.033276+00	\N	\N	\N	2025-11-25 19:51:01.07249+00	60.02038696471435	28.039214	{}	2025-11-25 19:50:33.036771+00	2025-11-25 19:51:01.076843+00
e82171b3-5990-498a-a15b-2a07cdaaab4d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.2603914617414	2025-11-25 22:02:33.758454+00	\N	\N	\N	2025-11-25 22:03:11.780424+00	56.04081829276972	38.02197	{}	2025-11-25 22:02:33.761526+00	2025-11-25 22:03:11.783485+00
8b06261e-8a90-4ef2-817f-7633b2fe6628	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.53287721143884	2025-11-25 19:52:41.156698+00	\N	\N	\N	2025-11-25 19:52:59.170058+00	66.42193652585748	18.01336	{}	2025-11-25 19:52:41.161209+00	2025-11-25 19:52:59.181229+00
7c47121f-df03-4f87-a66d-c99d339981fc	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.25276912217623	2025-11-25 20:49:17.333842+00	\N	\N	\N	2025-11-25 20:49:51.351502+00	62.6249269219452	34.01766	{}	2025-11-25 20:49:17.336473+00	2025-11-25 20:49:51.35514+00
124d83be-ea64-48d8-ae2b-b6261d1e2600	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.60120991384555	2025-11-25 19:53:01.175067+00	\N	\N	\N	2025-11-25 19:53:03.181089+00	65.49567730466764	2.006022	{}	2025-11-25 19:53:01.183956+00	2025-11-25 19:53:04.085908+00
0cfd6dbb-9587-4aa2-bb23-8be388698bcd	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.55778449434632	2025-11-25 21:13:24.138265+00	\N	\N	\N	2025-11-25 21:13:58.156875+00	55.46970739314863	34.01861	{}	2025-11-25 21:13:24.776146+00	2025-11-25 21:13:58.159651+00
0d1763fa-3e60-4e1e-849e-21a268bfe022	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.27367341795184	2025-11-25 19:53:39.209567+00	\N	\N	\N	2025-11-25 19:54:05.230795+00	64.0625833056212	26.021228	{}	2025-11-25 19:53:39.21973+00	2025-11-25 19:54:05.238188+00
50ba8814-2382-4082-828c-f56ba4dda6f1	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.89903037521007	2025-11-25 20:51:23.398942+00	\N	\N	\N	2025-11-25 20:52:01.422071+00	57.32199009105852	38.023129	{}	2025-11-25 20:51:23.404851+00	2025-11-25 20:52:01.427193+00
e5a1702b-249b-47da-96a7-53fd07d57b44	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.55772070152993	2025-11-25 23:04:23.726901+00	\N	\N	\N	2025-11-25 23:04:55.741849+00	62.25197089802093	32.014948	{}	2025-11-25 23:04:23.729542+00	2025-11-25 23:04:55.744313+00
97f9b195-6bce-48df-9c2e-51146b5c5504	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	72.28007477579482	2025-11-25 20:53:31.473974+00	\N	\N	\N	2025-11-25 20:54:03.493015+00	54.89659659346108	32.019041	{}	2025-11-25 20:53:31.477191+00	2025-11-25 20:54:03.4961+00
e5c30bea-405e-4862-8ad7-2f60a2951f58	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.42784298317349	2025-11-25 21:14:30.175466+00	\N	\N	\N	2025-11-25 21:14:52.186345+00	67.80088120341307	22.010879	{}	2025-11-25 21:14:30.178418+00	2025-11-25 21:14:52.18932+00
4b659ec3-15b3-4775-8c07-0fbcb6a91d6b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.75413721383734	2025-11-25 20:54:31.505399+00	\N	\N	\N	2025-11-25 20:55:05.526733+00	57.82807271317875	34.021334	{}	2025-11-25 20:54:31.508732+00	2025-11-25 20:55:05.530224+00
e58e1dcc-cb02-41fd-ac10-87119fc9a8c7	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.3254505271173	2025-11-25 22:03:39.795034+00	\N	\N	\N	2025-11-25 22:04:11.81553+00	61.913052752036506	32.020496	{}	2025-11-25 22:03:39.79759+00	2025-11-25 22:04:11.81865+00
13244310-8d8a-488a-baec-8e8a787f845d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	76.33528152487095	2025-11-25 21:15:32.20516+00	\N	\N	\N	2025-11-25 21:16:02.219596+00	56.62788744118197	30.014436	{}	2025-11-25 21:15:33.102058+00	2025-11-25 21:16:02.227257+00
b7cf3aa4-27bf-4f6b-838e-9ee2d5f10b3b	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.36307868959716	2025-11-25 21:36:28.907698+00	\N	\N	\N	2025-11-25 21:36:54.92215+00	63.82302238454524	26.014452	{}	2025-11-25 21:36:28.910771+00	2025-11-25 21:36:54.925496+00
4be7d964-8bad-4bc4-a33c-8ec116c6ea21	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.4833774409827	2025-11-25 22:04:41.828168+00	\N	\N	\N	2025-11-25 22:05:17.848241+00	55.998157342231096	36.020073	{}	2025-11-25 22:04:41.830856+00	2025-11-25 22:05:17.850968+00
8b4e8b5b-22d0-4f2a-b64d-62b1ec21629e	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.15344969585279	2025-11-25 21:37:30.944234+00	\N	\N	\N	2025-11-25 21:37:54.954317+00	66.73428701317602	24.010083	{}	2025-11-25 21:37:30.94729+00	2025-11-25 21:37:54.956951+00
aad04780-59ea-4c32-b83b-baffd234eb88	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.09919908256884	2025-11-25 23:06:25.789136+00	\N	\N	\N	2025-11-25 23:07:03.806868+00	61.283143173031135	38.017732	{}	2025-11-25 23:06:25.791739+00	2025-11-25 23:07:03.809513+00
d4ef4c45-96ae-4151-8a81-da1e9ed2c583	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.89865748275653	2025-11-25 21:39:33.005826+00	\N	\N	\N	2025-11-25 21:40:09.024628+00	60.54139343387215	36.018802	{}	2025-11-25 21:39:33.008029+00	2025-11-25 21:40:09.054084+00
55e24bb4-3761-47c1-a923-0dd756c7ce4a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.61238984338152	2025-11-25 22:06:43.893186+00	\N	\N	\N	2025-11-25 22:07:21.913384+00	58.87953215814448	38.020198	{}	2025-11-25 22:06:43.895891+00	2025-11-25 22:07:21.916118+00
ff4d8628-935a-4687-9b32-5d483c47a5c8	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.86437745697252	2025-11-25 21:42:49.113179+00	\N	\N	\N	2025-11-25 21:43:15.123779+00	57.947730876943304	26.0106	{}	2025-11-25 21:42:49.594476+00	2025-11-25 21:43:15.126703+00
aa2f5fee-a1fb-488c-b85f-73ef177b067b	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.99349056466264	2025-11-25 21:43:51.145698+00	\N	\N	\N	2025-11-25 21:44:13.156701+00	66.075044699587	22.011003	{}	2025-11-25 21:43:51.148439+00	2025-11-25 21:44:13.260725+00
8cf748c2-0b29-4270-9e6d-86daa1c26d4e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.94208624627801	2025-11-25 22:08:55.958968+00	\N	\N	\N	2025-11-25 22:09:25.977636+00	61.354583207876175	30.018668	{}	2025-11-25 22:08:55.962055+00	2025-11-25 22:09:25.980128+00
de441c99-524b-4ed9-b7c9-fff9100bc484	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.13143649511962	2025-11-25 23:17:00.125147+00	\N	\N	\N	2025-11-25 23:17:30.143456+00	64.90272200932445	30.018309	{}	2025-11-25 23:17:00.13382+00	2025-11-25 23:17:30.14606+00
7f85b7d4-e207-4428-917b-28abfd23dd2b	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.05439661313241	2025-11-25 22:09:57.99445+00	\N	\N	\N	2025-11-25 22:10:26.00941+00	62.17875327384705	28.01496	{}	2025-11-25 22:09:57.997221+00	2025-11-25 22:10:26.012+00
0679402d-7ad8-46e2-8597-1f409eba7132	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	78.91978761410061	2025-11-25 22:11:04.026987+00	\N	\N	\N	2025-11-25 22:11:32.040733+00	57.17327566238599	28.013746	{}	2025-11-25 22:11:04.02979+00	2025-11-25 22:11:32.043235+00
672d4365-4a24-468d-8f8c-21ea1cf1304e	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.65483917431843	2025-11-25 23:18:06.163059+00	\N	\N	\N	2025-11-25 23:18:32.17614+00	60.42752773409063	26.013081	{}	2025-11-25 23:18:06.165252+00	2025-11-25 23:18:32.179296+00
1d7c4c90-25e6-43d9-adce-76afa1266191	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.04633256776125	2025-11-25 22:12:06.059439+00	\N	\N	\N	2025-11-25 22:12:30.072554+00	66.06589804272983	24.013115	{}	2025-11-25 22:12:06.062151+00	2025-11-25 22:12:30.588749+00
984fe58d-b94e-44ff-9166-011a50904ce6	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.33355300222999	2025-11-25 22:14:08.124089+00	\N	\N	\N	2025-11-25 22:14:44.141886+00	58.22105855898147	36.017797	{}	2025-11-25 22:14:08.127392+00	2025-11-25 22:14:44.144788+00
be672d7e-b770-4a8e-ad97-9aec1a31410d	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.50649000383557	2025-11-25 23:19:04.193379+00	\N	\N	\N	2025-11-25 23:19:30.208505+00	65.62709203467604	26.015126	{}	2025-11-25 23:19:04.196337+00	2025-11-25 23:19:30.211218+00
09dbca56-0535-40e9-aeaf-649ffaf4dc37	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.87743712096365	2025-11-25 22:15:12.15619+00	\N	\N	\N	2025-11-25 22:15:46.171916+00	54.26888524220879	34.015726	{}	2025-11-25 22:15:12.158877+00	2025-11-25 22:15:46.174689+00
5fa3128c-99c3-4daf-a273-13a7e9c87b19	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.33125546804264	2025-11-25 22:37:42.882895+00	\N	\N	\N	2025-11-25 22:37:44.885017+00	56.42505647256621	2.002122	{}	2025-11-25 22:37:42.886446+00	2025-11-25 22:37:44.887301+00
e9f6bf98-3f3d-4aec-b635-c31b542a689b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.7737425718388	2025-11-25 23:20:08.23001+00	\N	\N	\N	2025-11-25 23:20:40.246799+00	54.82801267240557	32.016789	{}	2025-11-25 23:20:08.233039+00	2025-11-25 23:20:40.249449+00
9b176190-aac1-4b99-a642-a3e184cd07b7	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.22154541610746	2025-11-25 22:38:16.902578+00	\N	\N	\N	2025-11-25 22:38:44.916001+00	64.74390327751968	28.013423	{}	2025-11-25 22:38:16.905072+00	2025-11-25 22:38:44.91888+00
b6a5cbe8-843b-4104-95db-120eba00b779	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.98687244071239	2025-11-25 22:39:16.935528+00	\N	\N	\N	2025-11-25 22:39:42.95134+00	66.91984809946301	26.015812	{}	2025-11-25 22:39:16.938434+00	2025-11-25 22:39:42.953966+00
46a6f38e-673c-407b-ab49-15aea5d43498	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.99651593895425	2025-11-25 22:40:16.969767+00	\N	\N	\N	2025-11-25 22:40:50.990054+00	58.529402179413715	34.020287	{}	2025-11-25 22:40:16.972352+00	2025-11-25 22:40:51.472179+00
4bc151c4-cabd-4560-9303-dbb4706a6d93	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.28959079201975	2025-11-25 23:13:46.018709+00	\N	\N	\N	2025-11-25 23:14:22.038703+00	57.92479491343052	36.019994	{}	2025-11-25 23:13:46.021174+00	2025-11-25 23:14:22.041897+00
6a72f692-d459-484d-8678-9a8cb7afe114	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.01822498687245	2025-11-25 19:55:41.305699+00	\N	\N	\N	2025-11-25 19:56:07.327119+00	65.15163269957615	26.02142	{}	2025-11-25 19:55:41.314028+00	2025-11-25 19:56:07.335968+00
3c954765-e937-479b-8dfa-c78901c8cc82	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.60781366496688	2025-11-25 20:47:13.271598+00	\N	\N	\N	2025-11-25 20:47:43.286118+00	66.36801024611468	30.01452	{}	2025-11-25 20:47:13.276063+00	2025-11-25 20:47:43.289458+00
5882dc48-ebc3-4013-9073-7c126c1e1ac3	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.73605347963256	2025-11-25 19:56:47.367147+00	\N	\N	\N	2025-11-25 19:57:15.385034+00	60.03116773601839	28.017887	{}	2025-11-25 19:56:47.376425+00	2025-11-25 19:57:15.395362+00
a71e073f-4aac-4cc5-8268-6848e9eaf0b0	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.37577844095945	2025-11-25 21:18:36.305288+00	\N	\N	\N	2025-11-25 21:19:10.324727+00	56.60105113738236	34.019439	{}	2025-11-25 21:18:36.308144+00	2025-11-25 21:19:10.327658+00
3efa90c5-8c32-4f31-9c33-051154a0bb9b	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.6090078954914	2025-11-25 19:57:45.411246+00	\N	\N	\N	2025-11-25 19:58:13.433224+00	65.78197935915243	28.021978	{}	2025-11-25 19:57:45.419637+00	2025-11-25 19:58:13.439198+00
a55b6136-d4d3-4e05-8258-87c1239e7b28	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	72.11008240794862	2025-11-25 20:50:27.370903+00	\N	\N	\N	2025-11-25 20:50:55.384779+00	60.3504406500719	28.013876	{}	2025-11-25 20:50:27.378867+00	2025-11-25 20:50:55.388486+00
9a3a7933-8102-44d7-9e98-dc69612d3d8a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.9056004612602	2025-11-25 19:58:17.440159+00	\N	\N	\N	2025-11-25 19:58:19.444632+00	59.98855995538205	2.004473	{}	2025-11-25 19:58:17.449472+00	2025-11-25 19:58:19.448732+00
660fc84e-1ce2-4a6e-9564-53511f410785	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.45040423488464	2025-11-25 22:16:12.18479+00	\N	\N	\N	2025-11-25 22:16:42.20135+00	62.14097946013797	30.01656	{}	2025-11-25 22:16:12.187784+00	2025-11-25 22:16:42.204056+00
563ca374-5fa7-44ca-8356-d1b9091083b6	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.58210246655456	2025-11-25 20:52:29.441977+00	\N	\N	\N	2025-11-25 20:52:55.454899+00	65.96186329592236	26.012922	{}	2025-11-25 20:52:29.445123+00	2025-11-25 20:52:55.458332+00
c23a6780-5c25-42f8-9f0e-a1432eacdea0	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.40941462355343	2025-11-25 21:19:48.343928+00	\N	\N	\N	2025-11-25 21:20:06.351764+00	66.5069377456822	18.007836	{}	2025-11-25 21:19:48.347361+00	2025-11-25 21:20:06.494706+00
bd512481-6e2f-4bbc-9ed3-f8f5244574f8	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.12231681870234	2025-11-25 20:55:35.543142+00	\N	\N	\N	2025-11-25 20:56:07.563282+00	56.90086642581443	32.02014	{}	2025-11-25 20:55:35.546745+00	2025-11-25 20:56:07.566532+00
6e81bc51-fda5-4776-85f6-cbcc209c1be1	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.62250061173339	2025-11-25 20:56:35.578778+00	\N	\N	\N	2025-11-25 20:57:09.59835+00	62.49188470937714	34.019572	{}	2025-11-25 20:56:35.581938+00	2025-11-25 20:57:09.601345+00
18519718-9c45-4d3f-8be3-2aa0bf36d51b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.10587906210128	2025-11-25 21:20:40.36854+00	\N	\N	\N	2025-11-25 21:21:20.393767+00	53.17295437401046	40.025227	{}	2025-11-25 21:20:40.371261+00	2025-11-25 21:21:20.397116+00
a8ee2e54-3947-4b48-bcca-855193e355db	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.48882536248973	2025-11-25 20:57:45.617815+00	\N	\N	\N	2025-11-25 20:58:13.631511+00	55.81404416635422	28.013696	{}	2025-11-25 20:57:45.621106+00	2025-11-25 20:58:13.635279+00
f650f115-803a-42d2-9103-855e4117f98b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.48517029488623	2025-11-25 22:17:14.217015+00	\N	\N	\N	2025-11-25 22:17:52.23645+00	59.413579472343464	38.019435	{}	2025-11-25 22:17:14.218984+00	2025-11-25 22:17:52.239605+00
0ae5b520-4898-4fc6-8def-7a146c55ce35	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.60646436432548	2025-11-25 21:21:50.410192+00	\N	\N	\N	2025-11-25 21:22:16.423819+00	61.74024438228532	26.013627	{}	2025-11-25 21:21:50.416759+00	2025-11-25 21:22:16.426797+00
70c936f7-c1f2-4526-a2e7-ca42a7909799	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.02895849051643	2025-11-25 23:14:50.051827+00	\N	\N	\N	2025-11-25 23:15:26.072835+00	62.445778196253286	36.021008	{}	2025-11-25 23:14:50.053999+00	2025-11-25 23:15:26.075298+00
67bc5dec-2f56-4887-8bba-5751686c7acb	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.3322487339677	2025-11-25 21:22:50.44398+00	\N	\N	\N	2025-11-25 21:23:16.455938+00	64.2904056464708	26.011958	{}	2025-11-25 21:22:50.447033+00	2025-11-25 21:23:16.459164+00
b0da8b38-a792-48a1-95c1-dcd0d822687f	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.93478073578484	2025-11-25 22:18:20.251+00	\N	\N	\N	2025-11-25 22:18:50.267801+00	61.93439423072031	30.016801	{}	2025-11-25 22:18:20.253822+00	2025-11-25 22:18:50.275978+00
1a0eaa0f-f7a3-4613-88dd-400e03db80e1	968bfc86-180d-454f-8417-09f433813918	CLEARED	76.0837885825558	2025-11-25 21:30:14.693488+00	\N	\N	\N	2025-11-25 21:30:40.70945+00	63.14551285111768	26.015962	{}	2025-11-25 21:30:15.305142+00	2025-11-25 21:30:40.712739+00
504ce7d8-fbc9-4c78-87fb-5f07dbaa9761	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.20477199668863	2025-11-25 21:37:28.942436+00	\N	\N	\N	2025-11-25 21:38:04.962021+00	56.917695252117404	36.019585	{}	2025-11-25 21:37:28.945657+00	2025-11-25 21:38:04.964953+00
fc70b47d-efcc-4dd7-8153-a2e15a21bbdc	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.18822086028075	2025-11-25 22:20:32.316652+00	\N	\N	\N	2025-11-25 22:20:58.3294+00	56.80578564942442	26.012748	{}	2025-11-25 22:20:32.319134+00	2025-11-25 22:20:58.332+00
86bf3e21-e971-4ec4-b42c-f36a29d5344a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	73.15128059696009	2025-11-25 21:38:32.977051+00	\N	\N	\N	2025-11-25 21:39:06.992794+00	59.257834617762576	34.015743	{}	2025-11-25 21:38:32.980487+00	2025-11-25 21:39:06.9956+00
c4041628-db74-4cf3-b938-1f9e83c247c8	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.41332265015639	2025-11-25 23:15:54.085525+00	\N	\N	\N	2025-11-25 23:16:32.107577+00	57.901789274672495	38.022052	{}	2025-11-25 23:15:54.092342+00	2025-11-25 23:16:32.110305+00
3bc1a781-936d-42b1-9236-62ae18faff5a	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.71909272051809	2025-11-25 21:40:43.042011+00	\N	\N	\N	2025-11-25 21:41:07.056443+00	64.45172618307252	24.014432	{}	2025-11-25 21:40:43.044645+00	2025-11-25 21:41:07.059634+00
8f4ee75a-d25c-40d5-9cb6-3b7119681148	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.95620635871383	2025-11-25 22:21:30.346793+00	\N	\N	\N	2025-11-25 22:21:54.355811+00	64.60428290343054	24.009018	{}	2025-11-25 22:21:30.349141+00	2025-11-25 22:21:54.358417+00
dbc11a7c-f76b-48af-9276-c756b64b647e	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.37356825673284	2025-11-25 21:41:39.0788+00	\N	\N	\N	2025-11-25 21:42:19.097956+00	51.16007596225644	40.019156	{}	2025-11-25 21:41:39.08754+00	2025-11-25 21:42:19.100771+00
2b597be1-1213-4947-9a56-6c51aa463feb	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.5584024771233	2025-11-25 21:42:45.110499+00	\N	\N	\N	2025-11-25 21:43:21.128003+00	52.69248073770191	36.017504	{}	2025-11-25 21:42:45.113291+00	2025-11-25 21:43:21.682324+00
092946bb-0add-4d01-afc7-9822c6779ba8	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.77295788003786	2025-11-25 22:25:40.479377+00	\N	\N	\N	2025-11-25 22:26:08.494726+00	64.22701540325963	28.015349	{}	2025-11-25 22:25:40.481731+00	2025-11-25 22:26:08.624485+00
e925bd59-6268-4ac6-a9a4-c7fc07cc7ec5	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.88474001876304	2025-11-25 23:16:56.12072+00	\N	\N	\N	2025-11-25 23:16:58.123161+00	62.98668357916405	2.002441	{}	2025-11-25 23:16:56.123704+00	2025-11-25 23:16:58.125454+00
c3aa2dad-4603-4485-9429-4aa8627bccc9	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	70.10823067231107	2025-11-25 22:26:40.510345+00	\N	\N	\N	2025-11-25 22:27:12.528186+00	59.809175092641716	32.017841	{}	2025-11-25 22:26:40.706672+00	2025-11-25 22:27:12.793922+00
b1ee68d6-9a36-4eb5-9b07-9607ee934da2	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.36281842576913	2025-11-25 22:27:44.543696+00	\N	\N	\N	2025-11-25 22:27:48.546466+00	67.29183639156457	4.00277	{}	2025-11-25 22:27:44.951018+00	2025-11-25 22:27:48.549634+00
4b779167-5034-4c28-9783-a011a4b7cc66	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.42562116123779	2025-11-25 23:20:12.232277+00	\N	\N	\N	2025-11-25 23:20:34.243144+00	64.3904361037213	22.010867	{}	2025-11-25 23:20:12.235232+00	2025-11-25 23:20:34.246356+00
ff7dc718-8c95-4d17-b32b-1a509258e931	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.89227457708901	2025-11-25 22:29:54.618412+00	\N	\N	\N	2025-11-25 22:30:22.634977+00	59.553811815338314	28.016565	{}	2025-11-25 22:29:54.6259+00	2025-11-25 22:30:22.637567+00
3b09372a-0296-4c7d-8d8d-58ca2a5808ed	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.24888841800659	2025-11-25 22:39:46.954967+00	\N	\N	\N	2025-11-25 22:39:50.957723+00	58.4976964674237	4.002756	{}	2025-11-25 22:39:47.203375+00	2025-11-25 22:39:50.960619+00
66498164-d98b-4425-8aaf-48442a67ed0a	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.211452915693	2025-11-25 22:40:20.972895+00	\N	\N	\N	2025-11-25 22:40:44.985851+00	66.23524889516624	24.012956	{}	2025-11-25 22:40:20.975421+00	2025-11-25 22:40:44.988899+00
575c05c4-6f53-4ff6-801b-03bd4546b5b4	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	72.53483674759953	2025-11-25 22:41:23.005071+00	\N	\N	\N	2025-11-25 22:41:57.021166+00	55.70943542122898	34.016095	{}	2025-11-25 22:41:23.635662+00	2025-11-25 22:41:57.024093+00
07eb7cc9-4051-4837-ae80-b01d19e024ae	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.45617783441979	2025-11-25 22:42:27.037539+00	\N	\N	\N	2025-11-25 22:42:57.051914+00	57.83961038358319	30.014375	{}	2025-11-25 22:42:27.752056+00	2025-11-25 22:42:57.054734+00
6753365d-4445-47ba-989c-8b0ddd6370ae	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.47054128658493	2025-11-25 22:43:27.068491+00	\N	\N	\N	2025-11-25 22:43:59.08552+00	59.54407566386824	32.017029	{}	2025-11-25 22:43:27.071338+00	2025-11-25 22:43:59.08855+00
d9371024-4d78-4f39-bc26-18bdfce68ed9	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.56882507879345	2025-11-25 19:55:41.306084+00	\N	\N	\N	2025-11-25 19:56:11.335246+00	58.67499600894525	30.029162	{}	2025-11-25 19:55:41.32372+00	2025-11-25 19:56:11.343484+00
f5941e6d-7f55-419c-b108-d574eaaa7b19	968bfc86-180d-454f-8417-09f433813918	CLEARED	77.35314717608699	2025-11-25 20:48:19.305777+00	\N	\N	\N	2025-11-25 20:48:45.317395+00	62.33713056437816	26.011618	{}	2025-11-25 20:48:19.309312+00	2025-11-25 20:48:45.320952+00
e23cb823-d8d5-4f8a-af73-000908de4171	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.08974239487776	2025-11-25 19:58:47.460634+00	\N	\N	\N	2025-11-25 19:59:19.492976+00	61.243484092625984	32.032342	{}	2025-11-25 19:58:47.466046+00	2025-11-25 19:59:19.503635+00
f5a4c095-8236-467e-bb3a-038b7dcd9a5f	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.81909170194675	2025-11-25 21:18:40.308027+00	\N	\N	\N	2025-11-25 21:19:08.322166+00	66.6351345294056	28.014139	{}	2025-11-25 21:18:40.31058+00	2025-11-25 21:19:08.325557+00
8f5a6bbc-ade9-48bd-a3e4-77abd804f5e7	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.67516573955405	2025-11-25 20:49:19.337153+00	\N	\N	\N	2025-11-25 20:49:45.347804+00	65.42641019213472	26.010651	{}	2025-11-25 20:49:19.340504+00	2025-11-25 20:49:45.350754+00
77692184-31ee-40cf-b29c-25d0c0510284	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.46583329549473	2025-11-25 22:16:14.186702+00	\N	\N	\N	2025-11-25 22:16:40.199446+00	64.00631982071005	26.012744	{}	2025-11-25 22:16:15.065956+00	2025-11-25 22:16:40.201986+00
b7a4cf67-8861-48cc-804a-4ef9ddb032ce	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.22669475550276	2025-11-25 20:50:27.370832+00	\N	\N	\N	2025-11-25 20:50:55.384718+00	58.91365926734355	28.013886	{}	2025-11-25 20:50:27.373919+00	2025-11-25 20:50:55.393332+00
dc914d0b-a345-4c88-a0f8-da2886f04110	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.4813823686871	2025-11-25 21:20:48.373948+00	\N	\N	\N	2025-11-25 21:21:14.390295+00	62.31182301906398	26.016347	{}	2025-11-25 21:20:48.377007+00	2025-11-25 21:21:14.393286+00
b092a1e2-1797-4960-966f-eb4defdcbfd3	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.87087970153387	2025-11-25 20:51:27.404634+00	\N	\N	\N	2025-11-25 20:51:55.419119+00	65.32664836169913	28.014485	{}	2025-11-25 20:51:27.407705+00	2025-11-25 20:51:55.422371+00
a3c7bda4-ded4-47d5-9d14-fe0c5bcba238	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.94418936526111	2025-11-25 23:21:10.258861+00	\N	\N	\N	2025-11-25 23:21:36.271825+00	67.78334036367363	26.012964	{}	2025-11-25 23:21:10.261525+00	2025-11-25 23:21:36.274254+00
6a833263-e86f-4fff-a9ea-44bc386df257	968bfc86-180d-454f-8417-09f433813918	CLEARED	79.04861027349446	2025-11-25 20:53:35.476624+00	\N	\N	\N	2025-11-25 20:53:57.488757+00	66.36424354571528	22.012133	{}	2025-11-25 20:53:35.479388+00	2025-11-25 20:53:57.491776+00
6de9fe4a-3584-4d0f-82fc-d92072cbf73d	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	67.65518136665547	2025-11-25 21:28:02.613364+00	\N	\N	\N	2025-11-25 21:28:34.634827+00	62.28094189405227	32.021463	{}	2025-11-25 21:28:02.616234+00	2025-11-25 21:28:34.637578+00
ab06132c-283b-4786-b85e-0eeb5da1e2c7	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.88190727967486	2025-11-25 20:54:33.507583+00	\N	\N	\N	2025-11-25 20:54:35.509958+00	66.38914548558121	2.002375	{}	2025-11-25 20:54:33.510954+00	2025-11-25 20:54:35.51292+00
d815b96d-ddeb-4308-84b1-a042fd438f54	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.22360011489295	2025-11-25 22:18:20.250908+00	\N	\N	\N	2025-11-25 22:18:22.25349+00	67.1736452722489	2.002582	{}	2025-11-25 22:18:20.259405+00	2025-11-25 22:18:22.256332+00
30c385bd-a9e1-4fcc-8325-0430bed1c151	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.87685500867461	2025-11-25 20:57:39.613693+00	\N	\N	\N	2025-11-25 20:58:15.633905+00	56.4952589252746	36.020212	{}	2025-11-25 20:57:39.617028+00	2025-11-25 20:58:15.637092+00
d252541a-9b0e-4445-b89a-1736b8e305ab	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.0025330899329	2025-11-25 21:29:06.649453+00	\N	\N	\N	2025-11-25 21:29:08.651697+00	67.89353711002472	2.002244	{}	2025-11-25 21:29:06.652951+00	2025-11-25 21:29:08.654562+00
0fe7fb3a-9371-4693-8fd7-cf8db0e1510f	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.12275771231296	2025-11-25 21:29:10.654202+00	\N	\N	\N	2025-11-25 21:29:36.670905+00	63.134172859974214	26.016703	{}	2025-11-25 21:29:11.184837+00	2025-11-25 21:29:36.674226+00
55f5e4e1-a2e9-4247-884c-378b1e659c5b	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	68.96516720072185	2025-11-25 22:24:34.440045+00	\N	\N	\N	2025-11-25 22:25:10.459732+00	58.8915179835734	36.019687	{}	2025-11-25 22:24:34.442791+00	2025-11-25 22:25:10.461948+00
6387a93f-12b2-41c9-aa23-e34a509239c2	968bfc86-180d-454f-8417-09f433813918	CLEARED	72.14237141613411	2025-11-25 21:39:35.008112+00	\N	\N	\N	2025-11-25 21:40:09.02456+00	56.662962379518035	34.016448	{}	2025-11-25 21:39:35.011443+00	2025-11-25 21:40:09.036693+00
4a71124b-735f-4b11-b71e-c21ee15ac0a8	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.20730135854838	2025-11-25 23:24:18.354423+00	\N	\N	\N	2025-11-25 23:24:50.373835+00	60.812522596715176	32.019412	{}	2025-11-25 23:24:18.357241+00	2025-11-25 23:24:50.376357+00
89cb4637-3d5d-40ec-9302-8f0007bf7a91	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	71.54235568694084	2025-11-25 21:40:37.038314+00	\N	\N	\N	2025-11-25 21:41:07.056687+00	60.81108698096974	30.018373	{}	2025-11-25 21:40:37.041228+00	2025-11-25 21:41:07.06489+00
59f04257-6f64-4369-a8ac-28c90ac98404	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	65.73225880062307	2025-11-25 22:25:40.479443+00	\N	\N	\N	2025-11-25 22:26:08.494817+00	60.948025452691006	28.015374	{}	2025-11-25 22:25:40.486504+00	2025-11-25 22:26:08.614968+00
02aab877-c9b6-47a7-9450-5db7b8dc5d7d	968bfc86-180d-454f-8417-09f433813918	CLEARED	78.92821932084382	2025-11-25 22:26:46.513964+00	\N	\N	\N	2025-11-25 22:27:10.526302+00	66.33322332841044	24.012338	{}	2025-11-25 22:26:46.516316+00	2025-11-25 22:27:10.529095+00
b4f7144d-419a-4a0a-b634-6353999f6e40	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.65287370591288	2025-11-25 23:25:22.390044+00	\N	\N	\N	2025-11-25 23:25:54.405558+00	62.96751303498661	32.015514	{}	2025-11-25 23:25:22.393201+00	2025-11-25 23:25:54.408424+00
06e74f3b-a40d-44a8-b855-7bcfb3c6f741	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	69.12214493120183	2025-11-25 22:28:46.579764+00	\N	\N	\N	2025-11-25 22:29:16.599578+00	61.618222627452575	30.019814	{}	2025-11-25 22:28:46.582632+00	2025-11-25 22:29:16.601912+00
2d968f18-f86f-4139-8a27-69ace67de32a	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	66.29123567400767	2025-11-25 23:26:20.419215+00	\N	\N	\N	2025-11-25 23:26:56.443253+00	61.42890356724772	36.024038	{}	2025-11-25 23:26:20.422209+00	2025-11-25 23:26:56.446045+00
db49a03c-23c1-4fe1-8442-feadd2cda3f7	7e34a6fd-d1a2-4ec2-b955-9fe0917fe0b6	CLEARED	75.10052961019198	2025-11-25 23:27:32.462161+00	\N	\N	\N	2025-11-25 23:27:56.47561+00	60.815077832946294	24.013449	{}	2025-11-25 23:27:32.465418+00	2025-11-25 23:27:56.480895+00
d45a4826-4a11-4bda-a0a6-8e826bfa2234	968bfc86-180d-454f-8417-09f433813918	CLEARED	75.36380471347749	2025-11-25 23:28:32.496746+00	\N	\N	\N	2025-11-25 23:28:58.510543+00	60.51344760758767	26.013797	{}	2025-11-25 23:28:32.498845+00	2025-11-25 23:28:59.025315+00
2598fa19-1a81-4d06-8d3d-8b54b4d4280a	968bfc86-180d-454f-8417-09f433813918	ACTIVE	71.81867613528595	2025-11-25 23:29:34.530295+00	\N	\N	\N	\N	\N	\N	{}	2025-11-25 23:29:34.532631+00	2025-11-25 23:29:34.532631+00
e182d13f-dac7-4608-b285-c65b668ded23	968bfc86-180d-454f-8417-09f433813918	ACTIVE	74.72182297567757	2025-11-25 19:14:51.676589+00	\N	\N	\N	\N	\N	\N	{}	2025-11-25 19:15:02.717619+00	2025-11-25 19:15:02.717619+00
a588feba-c6c0-4156-832a-049e1f35ee00	968bfc86-180d-454f-8417-09f433813918	CLEARED	71.51240311288258	2025-11-25 19:17:02.780145+00	\N	\N	\N	2025-11-25 19:17:22.792431+00	65.35133193821875	20.012286	{}	2025-11-25 19:18:06.809488+00	2025-11-25 19:18:06.814459+00
b17ed7a7-b226-4c07-89e0-a9bdfb40189d	968bfc86-180d-454f-8417-09f433813918	CLEARED	74.61189507997351	2025-11-25 19:18:01.89321+00	\N	\N	\N	2025-11-25 19:18:25.90819+00	64.16085349201819	24.01498	{}	2025-11-25 19:18:06.818008+00	2025-11-25 19:18:25.921527+00
9c3f65a3-5d72-40cf-aba8-5037cf7dbbd0	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.03923204438074	2025-11-25 19:19:01.932057+00	\N	\N	\N	2025-11-25 19:19:03.937137+00	66.51523428758752	2.00508	{}	2025-11-25 19:19:01.944773+00	2025-11-25 19:19:04.0762+00
19609a4b-2c41-4280-bd4c-874734d0a715	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.26769698458199	2025-11-25 19:19:06.068132+00	\N	\N	\N	2025-11-25 19:19:30.086684+00	64.22271649275838	24.018552	{}	2025-11-25 19:19:06.081356+00	2025-11-25 19:19:30.097988+00
a78f253d-71aa-4aee-aa58-5f4e885716f2	968bfc86-180d-454f-8417-09f433813918	CLEARED	79.24547626337045	2025-11-25 19:20:10.11832+00	\N	\N	\N	2025-11-25 19:20:32.13908+00	65.521346210762	22.02076	{}	2025-11-25 19:20:10.129899+00	2025-11-25 19:20:32.15188+00
7f767b71-f2f9-4ebc-960f-4a7bf8dd09b8	968bfc86-180d-454f-8417-09f433813918	CLEARED	73.24229526383944	2025-11-25 19:21:08.166841+00	\N	\N	\N	2025-11-25 19:21:32.190304+00	66.48514347033341	24.023463	{}	2025-11-25 19:21:08.178212+00	2025-11-25 19:21:32.195296+00
3f658e0a-cecd-4b36-aff2-e48fcac2808b	968bfc86-180d-454f-8417-09f433813918	CLEARED	70.13509919566857	2025-11-25 19:22:12.214224+00	\N	\N	\N	2025-11-25 19:22:38.234427+00	63.25748482196345	26.020203	{}	2025-11-25 19:22:12.224006+00	2025-11-25 19:22:38.247224+00
\.


--
-- Data for Name: asset_attributes; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.asset_attributes (id, asset_id, name, description, attribute_type, tag_id, static_value, formula, unit, display_order, settings, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: asset_health_alerts; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.asset_health_alerts (id, asset_id, title, message, severity, state, health_score, health_status, issues_count, warnings_count, problematic_attributes, recommendations, alert_metadata, acknowledged_at, acknowledged_by, acknowledgment_comment, resolved_at, resolved_by, resolution_comment, resolved_health_score, notification_sent, notification_sent_at, auto_resolved, triggered_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: asset_health_history; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.asset_health_history (id, asset_id, snapshot_time, health_score, health_status, issues_count, warnings_count, attributes_evaluated, attribute_scores, issues_snapshot, warnings_snapshot, asset_metadata, health_score_change, trend_direction, velocity, created_at) FROM stdin;
\.


--
-- Data for Name: asset_templates; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.asset_templates (id, name, description, asset_type, attribute_definitions, analyses, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: assets; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.assets (id, name, description, asset_type, parent_id, template_id, is_active, asset_metadata, created_at, updated_at, path, level, icon, color, site_id, health_score, last_maintenance, next_maintenance, status) FROM stdin;
\.


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.conversations (id, user_id, organization_id, title, context, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: daily_operations; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.daily_operations (id, operation_date, trucks_received, trucks_total_tonnage, trucks_avg_wait_time, ships_in_port, ships_loading, ships_departed, ships_total_tonnage, total_tonnage_loaded, avg_loading_rate, operating_hours, downtime_hours, shiploaders_available, shiploaders_operating, conveyors_available, conveyors_operating, corn_tonnage, soy_tonnage, wheat_tonnage, other_tonnage, weather_condition, avg_temperature, rainfall_mm, wind_speed_kmh, weather_delays_hours, incidents_count, incidents_description, maintenance_hours, operational_efficiency, equipment_utilization, notes, site_id, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dashboard_shares; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.dashboard_shares (id, dashboard_id, user_id, can_edit, can_delete, created_at, shared_by) FROM stdin;
\.


--
-- Data for Name: dashboard_templates; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.dashboard_templates (id, name, description, module, config, thumbnail_url, is_active, is_system, usage_count, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dashboards; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.dashboards (id, user_id, organization_id, name, description, module, is_public, is_template, layout_config, default_filters, refresh_interval, auto_refresh, theme, show_legend, show_grid, view_count, last_viewed_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_imports; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.data_imports (id, data_source_id, import_type, file_name, file_size_bytes, status, records_total, records_imported, records_failed, records_duplicate, errors, warnings, requires_approval, approved_by, approved_at, approval_notes, started_at, completed_at, processing_duration_seconds, raw_data_sample, site_id, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_sources; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.data_sources (id, name, source_type, api_url, api_key_encrypted, auth_type, data_format, field_mapping, auto_sync, sync_interval_minutes, last_sync_at, last_sync_status, last_sync_error, validation_rules, require_approval, enabled, notes, site_id, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: devices; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.devices (id, site_id, name, description, protocol, is_active, connection_config, status, last_seen, error_message, manufacturer, model, serial_number, firmware_version, total_tags, data_points_collected, settings, created_at, updated_at) FROM stdin;
a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	\N	Simulator TEAG	\N	HTTP	t	{"port": 8000, "timeout": 5000, "endpoint": "http://localhost:8000/api/v1/simulator", "scan_rate": 1000, "ip_address": null, "description": "Terminal TEAG Simulator - Auto-registered", "endpoint_url": null}	UNKNOWN	\N	\N	\N	\N	\N	\N	0	0	{}	2025-11-13 01:38:04.072586+00	2025-11-13 01:38:04.072586+00
9b88e09b-dd9f-4b14-a5a8-78605a348da3	\N	Gateway-gateway-001	Gateway device for edge data collection (ID: gateway-001)	HTTP	t	{"type": "gateway", "endpoint": "http://optiflow-gateway:8080", "gateway_id": "gateway-001", "description": "Edge gateway for industrial data collection"}	CONNECTED	\N	\N	\N	\N	\N	\N	0	0	{}	2025-11-25 19:15:02.717619+00	2025-11-25 19:15:02.717619+00
\.


--
-- Data for Name: gateway_configs; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.gateway_configs (id, name, gateway_type, enabled, connection_config, polling_interval_ms, max_retries, base_retry_delay, max_buffer_size, description, created_at, updated_at) FROM stdin;
1	Terminal OPC-UA Gateway	OPCUA	t	{"endpoint": "opc.tcp://opcua-server:4840/optiflow/terminal", "namespace": "2", "security_policy": "None"}	1000	5	5	10000	Gateway de teste para terminal portuário	2025-11-04 03:08:44.277335+00	\N
2	Test OPC-UA Gateway	OPCUA	t	{"endpoint": "opc.tcp://opcua-server:4840/optiflow/terminal", "security_mode": "None", "security_policy": "None"}	1000	5	5	10000	Test gateway for manual configuration	2025-11-04 03:19:25.453801+00	\N
\.


--
-- Data for Name: gateway_health_logs; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.gateway_health_logs (id, gateway_name, "timestamp", status, successful_reads, failed_reads, buffer_size, uptime_seconds, last_error) FROM stdin;
\.


--
-- Data for Name: gateway_tags; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.gateway_tags (id, gateway_id, tag_name, enabled, address_config, data_type, scale_factor, "offset", unit, description, created_at) FROM stdin;
\.


--
-- Data for Name: gateway_tags_extended; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.gateway_tags_extended (id, gateway_id, tag_name, enabled, asset_id, tag_group, tag_type, address_config, data_type, scale_factor, tag_offset, formula, formula_tags, condition, unit, min_value, max_value, archive_enabled, archive_type, archive_deadband, archive_interval_seconds, compression_deviation, quality_enabled, alarm_enabled, alarm_config, description, category, properties, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: gbm_logistics_data; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.gbm_logistics_data (id, import_id, operation_type, external_id, external_reference, operation_date, completion_date, vehicle_id, vehicle_type, product_type, product_grade, gross_weight_kg, tare_weight_kg, net_weight_kg, moisture_percent, impurity_percent, protein_percent, broken_percent, quality_approved, quality_notes, origin, origin_city, origin_state, destination, destination_country, loading_time_minutes, waiting_time_minutes, total_time_minutes, throughput_kg_per_hour, freight_value, storage_value, service_value, total_value, status, berth_number, shiploader_id, conveyor_ids, contract_number, buyer_company, supplier_company, weather_condition, incidents, delays_description, notes, raw_data, validated, validated_by, validated_at, validation_notes, site_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.messages (id, conversation_id, role, content, message_metadata, created_at) FROM stdin;
\.


--
-- Data for Name: ml_models; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.ml_models (id, name, description, model_type, status, mlflow_run_id, mlflow_model_uri, version, algorithm, metrics, training_start, training_end, training_samples, feature_names, feature_importance, hyperparameters, deployed_at, is_active, retrain_frequency_days, last_retrain, next_retrain, settings, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.organizations (id, name, slug, description, is_active, contact_name, contact_email, contact_phone, settings, created_at, updated_at) FROM stdin;
f8b7f405-4f09-4f5f-ae3f-70f7f1975b27	OptiFlow Admin Organization	optiflow-admin	\N	t	\N	\N	\N	{}	2025-11-03 23:18:30.219762+00	2025-11-03 23:18:30.219762+00
91e5e4df-8e59-4a36-95fc-37617f697ff2	OptiFlow Demo	optiflow-demo	\N	t	\N	\N	\N	{}	2025-11-11 00:50:30.731502+00	2025-11-11 00:50:30.731502+00
\.


--
-- Data for Name: predictions; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.predictions (id, model_id, target_type, target_id, prediction_value, prediction_class, confidence, probabilities, features, shap_values, prediction_timestamp, prediction_horizon, actual_value, actual_class, outcome_timestamp, prediction_metadata, created_at) FROM stdin;
\.


--
-- Data for Name: ship_loadings; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.ship_loadings (id, ship_name, ship_imo, ship_flag, ship_dwt, berth_number, product_type, target_tonnage, loaded_tonnage, loading_rate_avg, loading_rate_peak, downtime_hours, arrival_time, berthing_time, loading_start_time, loading_end_time, departure_time, status, buyer_company, destination_port, destination_country, contract_number, average_moisture, average_impurity, quality_approved, quality_notes, weather_conditions, incidents, notes, site_id, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sites; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.sites (id, organization_id, name, slug, description, is_active, address, city, state, country, postal_code, latitude, longitude, site_type, settings, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tag_formulas; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.tag_formulas (id, name, description, formula_type, expression, input_tags, output_unit, output_type, execution_interval_seconds, is_active, category, tags_metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tag_labels; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.tag_labels (id, tag_id, display_name, short_name, equipment_name, area_name, system_name, custom_description, notes, is_visible, is_favorite, created_by, updated_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.tags (id, device_id, name, description, is_active, address, data_type, unit, category, min_value, max_value, engineering_min, engineering_max, scale, "offset", scan_rate_ms, deadband, enable_quality_check, last_value, last_quality, last_timestamp, data_points_count, settings, created_at, updated_at) FROM stdin;
722d6b36-0759-4ebe-8728-3654bdc9e5ba	9b88e09b-dd9f-4b14-a5a8-78605a348da3	LOAD_PCT_ALARM_TEST	Auto-created from Gateway alarm. Gateway tag ID: tag_load_pct	t	gateway:tag_load_pct	DOUBLE	%	ALARM	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-25 19:15:02.717619+00	2025-11-25 19:15:02.717619+00
3481b08a-a357-48fd-af5d-9aa4677b9564	9b88e09b-dd9f-4b14-a5a8-78605a348da3	por_carregamento	Auto-created from Gateway alarm. Gateway tag ID: tag_a4d574f8	t	gateway:tag_a4d574f8	DOUBLE	%	ALARM	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-25 19:40:06.465741+00	2025-11-25 19:40:06.465741+00
791c76d3-29ef-4578-87fb-3bd925bfd760	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV01_CURRENT_A_PV	current_a	t	ns=2;i=54	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
691305d6-0641-407a-8468-b583550820d4	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV01_POWER_KW_PV	power_kw	t	ns=2;i=55	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
0072deb7-b5ce-48a7-8b3f-84f59969be4e	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV01_TEMP_C_PV	temp_c	t	ns=2;i=56	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
773f9e14-6043-478f-abd8-15ecf1f2f431	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV02_RUNNING_PV	running	t	ns=2;i=58	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
cd78cac7-47e4-4875-8237-ea2185898ea5	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV02_BUCKET_SPEED_MPS_PV	bucket_speed_mps	t	ns=2;i=59	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
a29c65d3-133b-4779-97b2-1a97d7510385	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV02_CURRENT_A_PV	current_a	t	ns=2;i=60	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
33becf05-1e51-476d-8dc1-6bc381841616	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV02_POWER_KW_PV	power_kw	t	ns=2;i=61	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
791ad44b-d0d3-4d29-83b3-5cfb448f0e20	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV02_TEMP_C_PV	temp_c	t	ns=2;i=62	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
6d9816bd-ef09-4788-a473-9eeb4b6dab43	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	Energy_GRID_POWER_KW_PV	grid_power_kw	t	ns=2;i=63	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
2aeb3240-1614-463e-9591-ba63989c8dfa	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	Energy_TOTAL_ENERGY_KWH_PV	total_energy_kwh	t	ns=2;i=64	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
230ff2e3-3abc-40aa-90ac-c19397b1a077	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	Energy_POWER_FACTOR_PV	power_factor	t	ns=2;i=65	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
4b81795c-3a3b-450e-b7c8-55fd385290bb	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	Energy_GRID_VOLTAGE_V_PV	grid_voltage_v	t	ns=2;i=66	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
4f447126-8f7f-453d-a491-58ff2f6fa435	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_RUNNING_PV	running	t	ns=2;i=7	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
b4ddcfad-a67c-461c-b022-16b6f3a58013	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_SPEED_MPS_PV	speed_mps	t	ns=2;i=8	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
2ee0d241-85e4-463c-8ce8-8e68ddb12db3	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_LOAD_PCT_PV	load_pct	t	ns=2;i=9	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
6d17c6ae-515e-4adb-aa3b-808d2610a714	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_CURRENT_A_PV	current_a	t	ns=2;i=10	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
c95448dc-1a08-4f49-8219-b1fa218c2e5c	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_POWER_KW_PV	power_kw	t	ns=2;i=11	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
706713b4-08d9-4ff2-949b-49a73825decd	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_TEMP_C_PV	temp_c	t	ns=2;i=12	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
0edbef79-0ac4-424b-8d96-a4d8a15584cf	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_VIBRATION_MMS_PV	vibration_mms	t	ns=2;i=13	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
a2bb0a84-9f19-46ed-aec4-a4af468730a2	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR01_MISALIGNMENT_PV	misalignment	t	ns=2;i=14	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
f069f47f-0272-4a6e-8827-aa43de0bc2c0	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_RUNNING_PV	running	t	ns=2;i=16	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
83a10e7e-0fec-4f35-bad7-86ffc68a7060	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_SPEED_MPS_PV	speed_mps	t	ns=2;i=17	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
6a0f11f6-8e85-4606-a717-f82e9f33690a	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_LOAD_PCT_PV	load_pct	t	ns=2;i=18	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
c4b48fad-cec5-4b5b-affa-762d50f5adac	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_CURRENT_A_PV	current_a	t	ns=2;i=19	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
27b87267-0c43-4049-b3e2-4943c5bc4951	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_POWER_KW_PV	power_kw	t	ns=2;i=20	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
f56d626c-5808-4348-921b-0afa0413d6b6	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_TEMP_C_PV	temp_c	t	ns=2;i=21	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
cd72347e-e149-42e9-9361-1c630a7a2558	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_VIBRATION_MMS_PV	vibration_mms	t	ns=2;i=22	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
e7c8097e-7387-450e-941d-ad0770089559	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR02_MISALIGNMENT_PV	misalignment	t	ns=2;i=23	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
55820e37-0ab6-496c-914d-04bfe75e389a	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_RUNNING_PV	running	t	ns=2;i=25	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
5b49d35c-1dfe-4d15-93b8-fa5710d53d1d	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_SPEED_MPS_PV	speed_mps	t	ns=2;i=26	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
55662345-5000-4e22-b42c-39dc5a7c0e86	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_LOAD_PCT_PV	load_pct	t	ns=2;i=27	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
86b44062-e256-46ed-81a4-43aaf0e5acec	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_CURRENT_A_PV	current_a	t	ns=2;i=28	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
a5d80f25-7ea1-4d2d-9f31-60a5eeaac53c	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_POWER_KW_PV	power_kw	t	ns=2;i=29	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
abca2a0c-f522-4062-8a53-8dc9aff1c992	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_TEMP_C_PV	temp_c	t	ns=2;i=30	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
5c72cd4b-2a2c-4bea-bf34-ddd0af554bd4	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_VIBRATION_MMS_PV	vibration_mms	t	ns=2;i=31	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
1ba95dc1-6814-4ed9-a3c4-2890275350c6	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	CORR03_MISALIGNMENT_PV	misalignment	t	ns=2;i=32	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
15d23f28-3ac2-44e7-b4ff-f493151eb74c	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO01_LEVEL_PCT_PV	level_pct	t	ns=2;i=34	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
88d20c6f-aaa6-433a-a101-9c4551c10fe0	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO01_TEMP_GRAIN_C_PV	temp_grain_c	t	ns=2;i=35	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
5fecd825-f273-403b-91b4-4a913227a9f8	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO01_HUMIDITY_PCT_PV	humidity_pct	t	ns=2;i=36	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
328e9097-26dc-4a1a-b987-b4db67b69c99	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO01_WEIGHT_T_PV	weight_t	t	ns=2;i=37	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
55e3021a-8808-43b1-b942-92db82bab8a5	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO01_PRESSURE_PA_PV	pressure_pa	t	ns=2;i=38	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
9a4c2aaf-a569-4125-b781-ea10ae05de7f	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO02_LEVEL_PCT_PV	level_pct	t	ns=2;i=40	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
5350f561-7e6f-494e-b351-f9ea92b647d5	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO02_TEMP_GRAIN_C_PV	temp_grain_c	t	ns=2;i=41	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
f21c4eaa-dd17-4dc1-bfb1-fcb552a47531	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO02_HUMIDITY_PCT_PV	humidity_pct	t	ns=2;i=42	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
8e27c2fa-536d-4756-ac15-5e3f4aadd81e	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO02_WEIGHT_T_PV	weight_t	t	ns=2;i=43	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
a21e77fe-54cc-41d9-bae1-91acbeefe10a	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO02_PRESSURE_PA_PV	pressure_pa	t	ns=2;i=44	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
5944308e-2e53-4acb-b4ff-d5dfe14c0bba	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO03_LEVEL_PCT_PV	level_pct	t	ns=2;i=46	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
d0caa810-bd13-4022-b382-982bd321a7c0	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO03_TEMP_GRAIN_C_PV	temp_grain_c	t	ns=2;i=47	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
8b27b0f9-3b8c-4fc3-b710-77a1264693e3	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO03_HUMIDITY_PCT_PV	humidity_pct	t	ns=2;i=48	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
5ae7fa69-2348-42fa-9a00-8e5fe0f9ae59	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO03_WEIGHT_T_PV	weight_t	t	ns=2;i=49	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
b2764f80-9e08-4c74-bee6-f06033badd43	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	SILO03_PRESSURE_PA_PV	pressure_pa	t	ns=2;i=50	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
9feacf73-32c7-4f6f-b3da-dcdbc96689bc	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV01_RUNNING_PV	running	t	ns=2;i=52	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
957b2544-1cff-4573-810e-6119fa86a388	a7ffcef5-2a6e-414f-8a2a-ec2ffb941a93	ELEV01_BUCKET_SPEED_MPS_PV	bucket_speed_mps	t	ns=2;i=53	FLOAT	\N	PROCESS	\N	\N	\N	\N	1	0	1000	\N	t	\N	\N	\N	0	{}	2025-11-17 21:14:44.816412+00	2025-11-17 21:14:44.816412+00
\.


--
-- Data for Name: truck_entries; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.truck_entries (id, truck_id, driver_name, company, gross_weight, tare_weight, net_weight, product_type, product_quality, moisture_percent, impurity_percent, origin_farm, origin_city, origin_state, entry_time, gross_weight_time, tare_weight_time, exit_time, status, notes, site_id, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.users (id, organization_id, email, username, hashed_password, is_active, is_superuser, first_name, last_name, phone, role, last_login, failed_login_attempts, locked_until, preferences, created_at, updated_at) FROM stdin;
5f8432eb-50a8-4fa9-987d-8bcc8672b86c	f8b7f405-4f09-4f5f-ae3f-70f7f1975b27	admin@optiflow.com	admin	$2b$12$AWjoa/Zw9jAm9DSnmopaMu6zzF5IrF20Jx9PFNHe1cCQ7pTXxg0OK	t	t	Administrador	OptiFlow	\N	ADMIN	\N	0	\N	{}	2025-11-03 23:18:30.219762+00	2025-11-03 23:18:30.219762+00
\.


--
-- Data for Name: widgets; Type: TABLE DATA; Schema: public; Owner: optiflow
--

COPY public.widgets (id, dashboard_id, title, description, type, "position", grid_position, config, data_config, display_config, refresh_interval, created_at, updated_at) FROM stdin;
\.


--
-- Name: daily_operations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.daily_operations_id_seq', 1, false);


--
-- Name: data_imports_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.data_imports_id_seq', 1, false);


--
-- Name: data_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.data_sources_id_seq', 1, false);


--
-- Name: gateway_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.gateway_configs_id_seq', 2, true);


--
-- Name: gateway_health_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.gateway_health_logs_id_seq', 1, false);


--
-- Name: gateway_tags_extended_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.gateway_tags_extended_id_seq', 1, false);


--
-- Name: gateway_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.gateway_tags_id_seq', 220, true);


--
-- Name: gbm_logistics_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.gbm_logistics_data_id_seq', 1, false);


--
-- Name: ship_loadings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.ship_loadings_id_seq', 1, false);


--
-- Name: tag_formulas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.tag_formulas_id_seq', 1, false);


--
-- Name: truck_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: optiflow
--

SELECT pg_catalog.setval('public.truck_entries_id_seq', 1, false);


--
-- Name: alarm_definitions alarm_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.alarm_definitions
    ADD CONSTRAINT alarm_definitions_pkey PRIMARY KEY (id);


--
-- Name: alarm_events alarm_events_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.alarm_events
    ADD CONSTRAINT alarm_events_pkey PRIMARY KEY (id);


--
-- Name: asset_attributes asset_attributes_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_attributes
    ADD CONSTRAINT asset_attributes_pkey PRIMARY KEY (id);


--
-- Name: asset_health_alerts asset_health_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_health_alerts
    ADD CONSTRAINT asset_health_alerts_pkey PRIMARY KEY (id);


--
-- Name: asset_health_history asset_health_history_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_health_history
    ADD CONSTRAINT asset_health_history_pkey PRIMARY KEY (id);


--
-- Name: asset_templates asset_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_templates
    ADD CONSTRAINT asset_templates_pkey PRIMARY KEY (id);


--
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: daily_operations daily_operations_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.daily_operations
    ADD CONSTRAINT daily_operations_pkey PRIMARY KEY (id);


--
-- Name: dashboard_shares dashboard_shares_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboard_shares
    ADD CONSTRAINT dashboard_shares_pkey PRIMARY KEY (id);


--
-- Name: dashboard_templates dashboard_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboard_templates
    ADD CONSTRAINT dashboard_templates_pkey PRIMARY KEY (id);


--
-- Name: dashboards dashboards_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_pkey PRIMARY KEY (id);


--
-- Name: data_imports data_imports_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_pkey PRIMARY KEY (id);


--
-- Name: data_sources data_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_sources
    ADD CONSTRAINT data_sources_pkey PRIMARY KEY (id);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);


--
-- Name: gateway_configs gateway_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_configs
    ADD CONSTRAINT gateway_configs_pkey PRIMARY KEY (id);


--
-- Name: gateway_health_logs gateway_health_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_health_logs
    ADD CONSTRAINT gateway_health_logs_pkey PRIMARY KEY (id);


--
-- Name: gateway_tags_extended gateway_tags_extended_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_tags_extended
    ADD CONSTRAINT gateway_tags_extended_pkey PRIMARY KEY (id);


--
-- Name: gateway_tags gateway_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_tags
    ADD CONSTRAINT gateway_tags_pkey PRIMARY KEY (id);


--
-- Name: gbm_logistics_data gbm_logistics_data_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gbm_logistics_data
    ADD CONSTRAINT gbm_logistics_data_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: ml_models ml_models_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.ml_models
    ADD CONSTRAINT ml_models_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id);


--
-- Name: ship_loadings ship_loadings_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.ship_loadings
    ADD CONSTRAINT ship_loadings_pkey PRIMARY KEY (id);


--
-- Name: sites sites_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT sites_pkey PRIMARY KEY (id);


--
-- Name: tag_formulas tag_formulas_name_key; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.tag_formulas
    ADD CONSTRAINT tag_formulas_name_key UNIQUE (name);


--
-- Name: tag_formulas tag_formulas_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.tag_formulas
    ADD CONSTRAINT tag_formulas_pkey PRIMARY KEY (id);


--
-- Name: tag_labels tag_labels_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.tag_labels
    ADD CONSTRAINT tag_labels_pkey PRIMARY KEY (id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: truck_entries truck_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.truck_entries
    ADD CONSTRAINT truck_entries_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: widgets widgets_pkey; Type: CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT widgets_pkey PRIMARY KEY (id);


--
-- Name: idx_assets_health_score; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_health_score ON public.assets USING btree (health_score);


--
-- Name: idx_assets_last_maintenance; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_last_maintenance ON public.assets USING btree (last_maintenance);


--
-- Name: idx_assets_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_name ON public.assets USING btree (name);


--
-- Name: idx_assets_parent; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_parent ON public.assets USING btree (parent_id);


--
-- Name: idx_assets_path_new; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_path_new ON public.assets USING btree (path);


--
-- Name: idx_assets_site_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_site_id ON public.assets USING btree (site_id);


--
-- Name: idx_assets_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_status ON public.assets USING btree (status);


--
-- Name: idx_assets_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_assets_type ON public.assets USING btree (asset_type);


--
-- Name: idx_devices_protocol; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_devices_protocol ON public.devices USING btree (protocol, is_active);


--
-- Name: idx_gateway_tags_ext_asset; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_gateway_tags_ext_asset ON public.gateway_tags_extended USING btree (asset_id);


--
-- Name: idx_gateway_tags_ext_enabled; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_gateway_tags_ext_enabled ON public.gateway_tags_extended USING btree (enabled);


--
-- Name: idx_gateway_tags_ext_gateway; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_gateway_tags_ext_gateway ON public.gateway_tags_extended USING btree (gateway_id);


--
-- Name: idx_gateway_tags_ext_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_gateway_tags_ext_name ON public.gateway_tags_extended USING btree (tag_name);


--
-- Name: idx_gateway_tags_ext_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_gateway_tags_ext_type ON public.gateway_tags_extended USING btree (tag_type);


--
-- Name: idx_mv_alarm_stats_critical; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_alarm_stats_critical ON public.mv_alarm_statistics USING btree (critical_alarms DESC) WHERE (critical_alarms > 0);


--
-- Name: idx_mv_alarm_stats_date; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_alarm_stats_date ON public.mv_alarm_statistics USING btree (alarm_date DESC);


--
-- Name: idx_mv_alarm_stats_device; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_alarm_stats_device ON public.mv_alarm_statistics USING btree (device_id, alarm_date DESC);


--
-- Name: idx_mv_alarm_stats_tag; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_alarm_stats_tag ON public.mv_alarm_statistics USING btree (tag_id, alarm_date DESC);


--
-- Name: idx_mv_asset_health_score; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_asset_health_score ON public.mv_asset_health_overview USING btree (health_score DESC);


--
-- Name: idx_mv_asset_site; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_asset_site ON public.mv_asset_health_overview USING btree (site_id);


--
-- Name: idx_mv_daily_ops_date; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_daily_ops_date ON public.mv_daily_operations_summary USING btree (operation_date DESC);


--
-- Name: idx_mv_daily_ops_date_site; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_daily_ops_date_site ON public.mv_daily_operations_summary USING btree (operation_date, site_id);


--
-- Name: idx_mv_daily_ops_site; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_daily_ops_site ON public.mv_daily_operations_summary USING btree (site_id);


--
-- Name: idx_mv_tag_perf_category; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_tag_perf_category ON public.mv_tag_performance USING btree (category, is_active);


--
-- Name: idx_mv_tag_perf_datapoints; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_tag_perf_datapoints ON public.mv_tag_performance USING btree (data_points_count DESC);


--
-- Name: idx_mv_tag_perf_device; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_tag_perf_device ON public.mv_tag_performance USING btree (device_id, is_active);


--
-- Name: idx_mv_tag_perf_quality; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_tag_perf_quality ON public.mv_tag_performance USING btree (quality_status, data_freshness);


--
-- Name: idx_mv_tag_perf_stale; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_mv_tag_perf_stale ON public.mv_tag_performance USING btree (minutes_since_last_update DESC NULLS LAST) WHERE (is_active = true);


--
-- Name: idx_tag_formulas_active; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tag_formulas_active ON public.tag_formulas USING btree (is_active);


--
-- Name: idx_tag_formulas_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tag_formulas_name ON public.tag_formulas USING btree (name);


--
-- Name: idx_tag_formulas_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tag_formulas_type ON public.tag_formulas USING btree (formula_type);


--
-- Name: idx_tags_active; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tags_active ON public.tags USING btree (is_active, device_id);


--
-- Name: idx_tags_device_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tags_device_name ON public.tags USING btree (device_id, name);


--
-- Name: idx_tags_device_updated; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tags_device_updated ON public.tags USING btree (device_id, updated_at DESC);


--
-- Name: idx_tags_name_search; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tags_name_search ON public.tags USING btree (name text_pattern_ops);


--
-- Name: idx_tags_timestamp; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_tags_timestamp ON public.tags USING btree (last_timestamp DESC NULLS LAST) WHERE (is_active = true);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: ix_alarm_definitions_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_alarm_definitions_name ON public.alarm_definitions USING btree (name);


--
-- Name: ix_alarm_definitions_severity; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_alarm_definitions_severity ON public.alarm_definitions USING btree (severity);


--
-- Name: ix_alarm_definitions_tag_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_alarm_definitions_tag_id ON public.alarm_definitions USING btree (tag_id);


--
-- Name: ix_alarm_events_definition_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_alarm_events_definition_id ON public.alarm_events USING btree (definition_id);


--
-- Name: ix_alarm_events_state; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_alarm_events_state ON public.alarm_events USING btree (state);


--
-- Name: ix_alarm_events_trigger_timestamp; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_alarm_events_trigger_timestamp ON public.alarm_events USING btree (trigger_timestamp);


--
-- Name: ix_asset_attributes_asset_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_attributes_asset_id ON public.asset_attributes USING btree (asset_id);


--
-- Name: ix_asset_attributes_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_attributes_name ON public.asset_attributes USING btree (name);


--
-- Name: ix_asset_attributes_tag_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_attributes_tag_id ON public.asset_attributes USING btree (tag_id);


--
-- Name: ix_asset_health_alerts_asset_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_alerts_asset_id ON public.asset_health_alerts USING btree (asset_id);


--
-- Name: ix_asset_health_alerts_severity; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_alerts_severity ON public.asset_health_alerts USING btree (severity);


--
-- Name: ix_asset_health_alerts_state; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_alerts_state ON public.asset_health_alerts USING btree (state);


--
-- Name: ix_asset_health_alerts_triggered_at; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_alerts_triggered_at ON public.asset_health_alerts USING btree (triggered_at);


--
-- Name: ix_asset_health_history_asset_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_history_asset_id ON public.asset_health_history USING btree (asset_id);


--
-- Name: ix_asset_health_history_health_score; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_history_health_score ON public.asset_health_history USING btree (health_score);


--
-- Name: ix_asset_health_history_health_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_history_health_status ON public.asset_health_history USING btree (health_status);


--
-- Name: ix_asset_health_history_snapshot_time; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_health_history_snapshot_time ON public.asset_health_history USING btree (snapshot_time);


--
-- Name: ix_asset_templates_asset_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_asset_templates_asset_type ON public.asset_templates USING btree (asset_type);


--
-- Name: ix_asset_templates_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE UNIQUE INDEX ix_asset_templates_name ON public.asset_templates USING btree (name);


--
-- Name: ix_assets_asset_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_assets_asset_type ON public.assets USING btree (asset_type);


--
-- Name: ix_assets_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_assets_name ON public.assets USING btree (name);


--
-- Name: ix_assets_parent_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_assets_parent_id ON public.assets USING btree (parent_id);


--
-- Name: ix_assets_template_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_assets_template_id ON public.assets USING btree (template_id);


--
-- Name: ix_daily_operations_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_daily_operations_id ON public.daily_operations USING btree (id);


--
-- Name: ix_daily_operations_operation_date; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_daily_operations_operation_date ON public.daily_operations USING btree (operation_date);


--
-- Name: ix_dashboard_shares_dashboard_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_dashboard_shares_dashboard_id ON public.dashboard_shares USING btree (dashboard_id);


--
-- Name: ix_dashboard_shares_user_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_dashboard_shares_user_id ON public.dashboard_shares USING btree (user_id);


--
-- Name: ix_dashboard_templates_module; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_dashboard_templates_module ON public.dashboard_templates USING btree (module);


--
-- Name: ix_dashboards_module; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_dashboards_module ON public.dashboards USING btree (module);


--
-- Name: ix_dashboards_organization_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_dashboards_organization_id ON public.dashboards USING btree (organization_id);


--
-- Name: ix_dashboards_user_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_dashboards_user_id ON public.dashboards USING btree (user_id);


--
-- Name: ix_data_imports_data_source_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_data_imports_data_source_id ON public.data_imports USING btree (data_source_id);


--
-- Name: ix_data_imports_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_data_imports_id ON public.data_imports USING btree (id);


--
-- Name: ix_data_imports_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_data_imports_status ON public.data_imports USING btree (status);


--
-- Name: ix_data_sources_enabled; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_data_sources_enabled ON public.data_sources USING btree (enabled);


--
-- Name: ix_data_sources_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_data_sources_id ON public.data_sources USING btree (id);


--
-- Name: ix_data_sources_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_data_sources_name ON public.data_sources USING btree (name);


--
-- Name: ix_data_sources_source_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_data_sources_source_type ON public.data_sources USING btree (source_type);


--
-- Name: ix_devices_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_devices_name ON public.devices USING btree (name);


--
-- Name: ix_devices_protocol; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_devices_protocol ON public.devices USING btree (protocol);


--
-- Name: ix_devices_site_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_devices_site_id ON public.devices USING btree (site_id);


--
-- Name: ix_devices_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_devices_status ON public.devices USING btree (status);


--
-- Name: ix_gateway_configs_gateway_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gateway_configs_gateway_type ON public.gateway_configs USING btree (gateway_type);


--
-- Name: ix_gateway_configs_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gateway_configs_id ON public.gateway_configs USING btree (id);


--
-- Name: ix_gateway_configs_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE UNIQUE INDEX ix_gateway_configs_name ON public.gateway_configs USING btree (name);


--
-- Name: ix_gateway_health_logs_gateway_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gateway_health_logs_gateway_name ON public.gateway_health_logs USING btree (gateway_name);


--
-- Name: ix_gateway_health_logs_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gateway_health_logs_id ON public.gateway_health_logs USING btree (id);


--
-- Name: ix_gateway_health_logs_timestamp; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gateway_health_logs_timestamp ON public.gateway_health_logs USING btree ("timestamp");


--
-- Name: ix_gateway_tags_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gateway_tags_id ON public.gateway_tags USING btree (id);


--
-- Name: ix_gateway_tags_tag_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gateway_tags_tag_name ON public.gateway_tags USING btree (tag_name);


--
-- Name: ix_gbm_logistics_data_external_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_external_id ON public.gbm_logistics_data USING btree (external_id);


--
-- Name: ix_gbm_logistics_data_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_id ON public.gbm_logistics_data USING btree (id);


--
-- Name: ix_gbm_logistics_data_import_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_import_id ON public.gbm_logistics_data USING btree (import_id);


--
-- Name: ix_gbm_logistics_data_operation_date; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_operation_date ON public.gbm_logistics_data USING btree (operation_date);


--
-- Name: ix_gbm_logistics_data_operation_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_operation_type ON public.gbm_logistics_data USING btree (operation_type);


--
-- Name: ix_gbm_logistics_data_product_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_product_type ON public.gbm_logistics_data USING btree (product_type);


--
-- Name: ix_gbm_logistics_data_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_status ON public.gbm_logistics_data USING btree (status);


--
-- Name: ix_gbm_logistics_data_validated; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_gbm_logistics_data_validated ON public.gbm_logistics_data USING btree (validated);


--
-- Name: ix_ml_models_mlflow_run_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ml_models_mlflow_run_id ON public.ml_models USING btree (mlflow_run_id);


--
-- Name: ix_ml_models_model_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ml_models_model_type ON public.ml_models USING btree (model_type);


--
-- Name: ix_ml_models_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ml_models_name ON public.ml_models USING btree (name);


--
-- Name: ix_ml_models_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ml_models_status ON public.ml_models USING btree (status);


--
-- Name: ix_organizations_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE UNIQUE INDEX ix_organizations_name ON public.organizations USING btree (name);


--
-- Name: ix_organizations_slug; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE UNIQUE INDEX ix_organizations_slug ON public.organizations USING btree (slug);


--
-- Name: ix_predictions_model_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_predictions_model_id ON public.predictions USING btree (model_id);


--
-- Name: ix_predictions_prediction_timestamp; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_predictions_prediction_timestamp ON public.predictions USING btree (prediction_timestamp);


--
-- Name: ix_predictions_target_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_predictions_target_id ON public.predictions USING btree (target_id);


--
-- Name: ix_predictions_target_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_predictions_target_type ON public.predictions USING btree (target_type);


--
-- Name: ix_ship_loadings_arrival_time; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ship_loadings_arrival_time ON public.ship_loadings USING btree (arrival_time);


--
-- Name: ix_ship_loadings_berth_number; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ship_loadings_berth_number ON public.ship_loadings USING btree (berth_number);


--
-- Name: ix_ship_loadings_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ship_loadings_id ON public.ship_loadings USING btree (id);


--
-- Name: ix_ship_loadings_product_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ship_loadings_product_type ON public.ship_loadings USING btree (product_type);


--
-- Name: ix_ship_loadings_ship_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ship_loadings_ship_name ON public.ship_loadings USING btree (ship_name);


--
-- Name: ix_ship_loadings_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_ship_loadings_status ON public.ship_loadings USING btree (status);


--
-- Name: ix_sites_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_sites_name ON public.sites USING btree (name);


--
-- Name: ix_sites_organization_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_sites_organization_id ON public.sites USING btree (organization_id);


--
-- Name: ix_sites_site_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_sites_site_type ON public.sites USING btree (site_type);


--
-- Name: ix_sites_slug; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_sites_slug ON public.sites USING btree (slug);


--
-- Name: ix_tag_labels_area_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_tag_labels_area_name ON public.tag_labels USING btree (area_name);


--
-- Name: ix_tag_labels_display_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_tag_labels_display_name ON public.tag_labels USING btree (display_name);


--
-- Name: ix_tag_labels_equipment_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_tag_labels_equipment_name ON public.tag_labels USING btree (equipment_name);


--
-- Name: ix_tag_labels_system_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_tag_labels_system_name ON public.tag_labels USING btree (system_name);


--
-- Name: ix_tag_labels_tag_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE UNIQUE INDEX ix_tag_labels_tag_id ON public.tag_labels USING btree (tag_id);


--
-- Name: ix_tags_category; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_tags_category ON public.tags USING btree (category);


--
-- Name: ix_tags_device_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_tags_device_id ON public.tags USING btree (device_id);


--
-- Name: ix_tags_name; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_tags_name ON public.tags USING btree (name);


--
-- Name: ix_truck_entries_entry_time; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_truck_entries_entry_time ON public.truck_entries USING btree (entry_time);


--
-- Name: ix_truck_entries_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_truck_entries_id ON public.truck_entries USING btree (id);


--
-- Name: ix_truck_entries_product_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_truck_entries_product_type ON public.truck_entries USING btree (product_type);


--
-- Name: ix_truck_entries_status; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_truck_entries_status ON public.truck_entries USING btree (status);


--
-- Name: ix_truck_entries_truck_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_truck_entries_truck_id ON public.truck_entries USING btree (truck_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_organization_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_users_organization_id ON public.users USING btree (organization_id);


--
-- Name: ix_users_role; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_users_role ON public.users USING btree (role);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_widgets_dashboard_id; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_widgets_dashboard_id ON public.widgets USING btree (dashboard_id);


--
-- Name: ix_widgets_type; Type: INDEX; Schema: public; Owner: optiflow
--

CREATE INDEX ix_widgets_type ON public.widgets USING btree (type);


--
-- Name: assets update_assets_updated_at; Type: TRIGGER; Schema: public; Owner: optiflow
--

CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON public.assets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: gateway_tags_extended update_gateway_tags_ext_updated_at; Type: TRIGGER; Schema: public; Owner: optiflow
--

CREATE TRIGGER update_gateway_tags_ext_updated_at BEFORE UPDATE ON public.gateway_tags_extended FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: tag_formulas update_tag_formulas_updated_at; Type: TRIGGER; Schema: public; Owner: optiflow
--

CREATE TRIGGER update_tag_formulas_updated_at BEFORE UPDATE ON public.tag_formulas FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: alarm_definitions alarm_definitions_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.alarm_definitions
    ADD CONSTRAINT alarm_definitions_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: alarm_events alarm_events_acknowledged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.alarm_events
    ADD CONSTRAINT alarm_events_acknowledged_by_fkey FOREIGN KEY (acknowledged_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: alarm_events alarm_events_definition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.alarm_events
    ADD CONSTRAINT alarm_events_definition_id_fkey FOREIGN KEY (definition_id) REFERENCES public.alarm_definitions(id) ON DELETE CASCADE;


--
-- Name: asset_attributes asset_attributes_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_attributes
    ADD CONSTRAINT asset_attributes_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: asset_attributes asset_attributes_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_attributes
    ADD CONSTRAINT asset_attributes_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE SET NULL;


--
-- Name: asset_health_alerts asset_health_alerts_acknowledged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_health_alerts
    ADD CONSTRAINT asset_health_alerts_acknowledged_by_fkey FOREIGN KEY (acknowledged_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: asset_health_alerts asset_health_alerts_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_health_alerts
    ADD CONSTRAINT asset_health_alerts_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: asset_health_alerts asset_health_alerts_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_health_alerts
    ADD CONSTRAINT asset_health_alerts_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: asset_health_history asset_health_history_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.asset_health_history
    ADD CONSTRAINT asset_health_history_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: assets assets_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: assets assets_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.asset_templates(id);


--
-- Name: conversations conversations_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: daily_operations daily_operations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.daily_operations
    ADD CONSTRAINT daily_operations_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: daily_operations daily_operations_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.daily_operations
    ADD CONSTRAINT daily_operations_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: dashboard_shares dashboard_shares_dashboard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboard_shares
    ADD CONSTRAINT dashboard_shares_dashboard_id_fkey FOREIGN KEY (dashboard_id) REFERENCES public.dashboards(id) ON DELETE CASCADE;


--
-- Name: dashboard_shares dashboard_shares_shared_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboard_shares
    ADD CONSTRAINT dashboard_shares_shared_by_fkey FOREIGN KEY (shared_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: dashboard_shares dashboard_shares_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboard_shares
    ADD CONSTRAINT dashboard_shares_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: dashboards dashboards_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: dashboards dashboards_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: data_imports data_imports_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: data_imports data_imports_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: data_imports data_imports_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.data_sources(id);


--
-- Name: data_imports data_imports_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: data_sources data_sources_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_sources
    ADD CONSTRAINT data_sources_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: data_sources data_sources_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.data_sources
    ADD CONSTRAINT data_sources_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: devices devices_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE CASCADE;


--
-- Name: gateway_tags_extended gateway_tags_extended_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_tags_extended
    ADD CONSTRAINT gateway_tags_extended_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE SET NULL;


--
-- Name: gateway_tags_extended gateway_tags_extended_gateway_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_tags_extended
    ADD CONSTRAINT gateway_tags_extended_gateway_id_fkey FOREIGN KEY (gateway_id) REFERENCES public.gateway_configs(id) ON DELETE CASCADE;


--
-- Name: gateway_tags gateway_tags_gateway_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gateway_tags
    ADD CONSTRAINT gateway_tags_gateway_id_fkey FOREIGN KEY (gateway_id) REFERENCES public.gateway_configs(id) ON DELETE CASCADE;


--
-- Name: gbm_logistics_data gbm_logistics_data_import_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gbm_logistics_data
    ADD CONSTRAINT gbm_logistics_data_import_id_fkey FOREIGN KEY (import_id) REFERENCES public.data_imports(id);


--
-- Name: gbm_logistics_data gbm_logistics_data_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gbm_logistics_data
    ADD CONSTRAINT gbm_logistics_data_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: gbm_logistics_data gbm_logistics_data_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.gbm_logistics_data
    ADD CONSTRAINT gbm_logistics_data_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(id);


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: predictions predictions_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.ml_models(id) ON DELETE CASCADE;


--
-- Name: ship_loadings ship_loadings_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.ship_loadings
    ADD CONSTRAINT ship_loadings_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: ship_loadings ship_loadings_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.ship_loadings
    ADD CONSTRAINT ship_loadings_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: sites sites_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT sites_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: tag_labels tag_labels_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.tag_labels
    ADD CONSTRAINT tag_labels_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: tags tags_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: truck_entries truck_entries_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.truck_entries
    ADD CONSTRAINT truck_entries_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: truck_entries truck_entries_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.truck_entries
    ADD CONSTRAINT truck_entries_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: widgets widgets_dashboard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optiflow
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT widgets_dashboard_id_fkey FOREIGN KEY (dashboard_id) REFERENCES public.dashboards(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: optiflow
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: mv_alarm_statistics; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: optiflow
--

REFRESH MATERIALIZED VIEW public.mv_alarm_statistics;


--
-- Name: mv_asset_health_overview; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: optiflow
--

REFRESH MATERIALIZED VIEW public.mv_asset_health_overview;


--
-- Name: mv_daily_operations_summary; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: optiflow
--

REFRESH MATERIALIZED VIEW public.mv_daily_operations_summary;


--
-- Name: mv_tag_performance; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: optiflow
--

REFRESH MATERIALIZED VIEW public.mv_tag_performance;


--
-- PostgreSQL database dump complete
--

\unrestrict mmfxgPDBtU0JgMfiVyco5H90rSKzGkTJMmekMDdHpWWmkjA9Puw5828N3jfObfR

