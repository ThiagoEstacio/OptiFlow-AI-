"""
Data processing tasks for Celery
"""
from celery import shared_task
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sqlalchemy import create_engine, text
import logging
import os

logger = logging.getLogger(__name__)

# InfluxDB configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "optiflow-super-secret-token-change-in-production")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "optiflow")

# PostgreSQL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://optiflow:optiflow_password@postgres:5432/optiflow")


@shared_task(name="process_gateway_message")
def process_gateway_message(message_data: dict):
    """
    Process incoming message from gateway
    
    Saves data to:
    1. InfluxDB (time-series storage)
    2. PostgreSQL (last_value update)
    
    Args:
        message_data: Message payload from RabbitMQ
        Expected format: {
            "tag_name": "CORR01.temp_c",
            "value": 45.2,
            "quality": "GOOD",
            "timestamp": "2025-11-17T19:00:00Z"
        }
    """
    try:
        tag_name = message_data.get('tag_name')
        value = message_data.get('value')
        quality = message_data.get('quality', 'GOOD')
        timestamp_str = message_data.get('timestamp')
        
        if not tag_name or value is None:
            logger.warning(f"Invalid message data: {message_data}")
            return {"status": "error", "message": "Missing tag_name or value"}
        
        # Parse timestamp
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        # 1. Save to InfluxDB
        try:
            with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                
                point = Point("tag_values") \
                    .tag("tag_name", tag_name) \
                    .field("value", float(value)) \
                    .field("quality", quality) \
                    .time(timestamp)
                
                write_api.write(bucket=INFLUXDB_BUCKET, record=point)
                logger.debug(f"✅ Saved to InfluxDB: {tag_name} = {value}")
        except Exception as e:
            logger.error(f"❌ InfluxDB error for {tag_name}: {e}")
        
        # 2. Update PostgreSQL last_value
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        UPDATE tags 
                        SET 
                            last_value = :value,
                            last_quality = :quality,
                            last_timestamp = :timestamp,
                            updated_at = NOW()
                        WHERE name = :tag_name
                    """),
                    {
                        "value": str(value),
                        "quality": quality,
                        "timestamp": timestamp,
                        "tag_name": tag_name
                    }
                )
                conn.commit()
                logger.debug(f"✅ Updated PostgreSQL: {tag_name} = {value}")
        except Exception as e:
            logger.error(f"❌ PostgreSQL error for {tag_name}: {e}")
        
        return {
            "status": "success",
            "tag_name": tag_name,
            "value": value,
            "timestamp": timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing message: {e}", exc_info=True)
        raise


@shared_task(name="cleanup_old_data")
def cleanup_old_data(days: int = 90):
    """
    Clean up old timeseries data from InfluxDB
    
    Args:
        days: Number of days to retain
    """
    try:
        logger.info(f"Cleaning up data older than {days} days")
        # TODO: Implement cleanup logic
        return {"status": "success", "days": days}
    except Exception as e:
        logger.error(f"Error cleaning up data: {e}")
        raise


@shared_task(name="refresh_materialized_views")
def refresh_materialized_views():
    """
    Refresh PostgreSQL materialized views
    """
    try:
        logger.info("Refreshing materialized views")
        # TODO: Implement refresh logic (non-concurrent for now)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error refreshing views: {e}")
        raise
