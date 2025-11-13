"""
Application configuration using Pydantic Settings with HashiCorp Vault integration
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with Vault integration"""

    # Vault Configuration
    VAULT_ENABLED: bool = True
    VAULT_ADDR: str = "http://vault:8200"
    VAULT_TOKEN: str = "optiflow-dev-root-token"

    # Application
    APP_NAME: str = "OptiFlow AI Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database - PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://optiflow:optiflow_password@localhost:5432/optiflow"
    DATABASE_POOL_SIZE: int = 50  # ✅ Increased from 20 for 250+ concurrent users
    DATABASE_MAX_OVERFLOW: int = 100  # ✅ Increased from 40 for burst handling
    DATABASE_POOL_TIMEOUT: int = 30  # Connection pool timeout in seconds
    DATABASE_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    DATABASE_POOL_PRE_PING: bool = True  # Test connections before using
    DATABASE_ECHO_POOL: bool = True  # ✅ Monitor pool usage in logs
    DATABASE_CONNECT_TIMEOUT: int = 10  # Connection timeout in seconds
    DATABASE_COMMAND_TIMEOUT: int = 30  # Query execution timeout in seconds

    # Database - InfluxDB
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""
    INFLUXDB_ORG: str = "optiflow"
    INFLUXDB_BUCKET: str = "timeseries"
    INFLUXDB_BUCKET_AGGREGATIONS: str = "aggregations"
    INFLUXDB_BUCKET_DOWNSAMPLED: str = "downsampled"

    # Database - Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_DB: int = 1
    REDIS_SESSION_DB: int = 2
    REDIS_REALTIME_DB: int = 3

    # Message Queue - RabbitMQ
    RABBITMQ_URL: str = "amqp://optiflow:optiflow_password@localhost:5672/"
    CELERY_BROKER_URL: str = "amqp://optiflow:optiflow_password@localhost:5672/"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/4"

    # Security
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # WebSocket
    WEBSOCKET_PING_INTERVAL: int = 25
    WEBSOCKET_PING_TIMEOUT: int = 60

    # ML / MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "optiflow-ml"
    ML_MODEL_REGISTRY: str = "models"

    # AI / OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7

    # AI / Ollama (local LLM)
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    USE_OLLAMA: bool = True  # Set to True to use Ollama instead of OpenAI

    # Gateway
    GATEWAY_API_KEY: str = "secure-gateway-api-key-change-in-production"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Request Timeout & Resilience
    REQUEST_TIMEOUT_SECONDS: int = 30  # Maximum request processing time
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5  # Failures before opening circuit
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # Seconds before trying to recover
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = "Exception"  # Exception to catch

    # Email (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # SMS (for critical alarms)
    SMS_PROVIDER: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Data Retention
    TIMESERIES_RETENTION_DAYS: int = 365
    AGGREGATIONS_RETENTION_DAYS: int = 1825
    DOWNSAMPLED_RETENTION_DAYS: int = 3650
    ALARM_HISTORY_RETENTION_DAYS: int = 730

    # ========================================
    # Gateway Service Configuration
    # ========================================
    GATEWAY_ENABLED: bool = True
    GATEWAY_POLL_INTERVAL_S: float = 1.0
    GATEWAY_SOURCE_NAME: str = "optiflow-gateway"
    GATEWAY_MAX_BUFFER_SIZE: int = 10000
    
    # Circuit Breaker
    GATEWAY_CIRCUIT_BREAKER_THRESHOLD: int = 5
    GATEWAY_CIRCUIT_BREAKER_TIMEOUT_S: int = 30
    
    # Retry Configuration
    GATEWAY_MAX_RETRY_ATTEMPTS: int = 3
    GATEWAY_RETRY_BACKOFF_FACTOR: float = 2.0
    
    # Rate Limiting
    GATEWAY_RATE_LIMIT_MSGS_PER_SEC: Optional[int] = None
    
    # Tag Discovery
    GATEWAY_TAG_DISCOVERY_INTERVAL_S: int = 60
    
    # Buffer Flush
    GATEWAY_BUFFER_FLUSH_INTERVAL_S: int = 5
    
    # ========================================
    # Consumer Service Configuration
    # ========================================
    CONSUMER_ENABLED: bool = True
    CONSUMER_TOPIC: str = "raw_tags"
    CONSUMER_GROUP_ID: str = "timeseries-writers"
    
    # Batch Configuration
    CONSUMER_MIN_BATCH_SIZE: int = 50
    CONSUMER_MAX_BATCH_SIZE: int = 500
    CONSUMER_BATCH_TIMEOUT_S: float = 5.0
    
    # Deduplication
    CONSUMER_DEDUP_CACHE_SIZE: int = 10000
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_DLQ_TOPIC: str = "raw_tags_dlq"

    def __init__(self, **kwargs):
        """Initialize settings with Vault integration."""
        super().__init__(**kwargs)

        # Only try to load from Vault if enabled
        if not self.VAULT_ENABLED:
            logger.info("⚙️ Vault disabled - using environment variables")
            return

        try:
            from app.core.vault import get_vault_client

            vault = get_vault_client()
            if not vault.is_authenticated():
                logger.warning("⚠️ Vault not authenticated - using environment fallback")
                return

            logger.info("🔐 Loading secrets from Vault...")

            # Database URLs
            postgres_url = vault.get_database_url("postgres")
            if postgres_url:
                self.DATABASE_URL = postgres_url
                logger.debug("✅ PostgreSQL URL loaded from Vault")

            influxdb_url = vault.get_secret("database/influxdb", "url")
            if influxdb_url:
                self.INFLUXDB_URL = influxdb_url

            influxdb_token = vault.get_secret("database/influxdb", "token")
            if influxdb_token:
                self.INFLUXDB_TOKEN = influxdb_token
                logger.debug("✅ InfluxDB credentials loaded from Vault")

            # Redis URL
            redis_url = vault.get_redis_url()
            if redis_url:
                self.REDIS_URL = redis_url
                logger.debug("✅ Redis URL loaded from Vault")

            # RabbitMQ URLs
            rabbitmq_url = vault.get_rabbitmq_url()
            if rabbitmq_url:
                self.RABBITMQ_URL = rabbitmq_url
                self.CELERY_BROKER_URL = rabbitmq_url
                logger.debug("✅ RabbitMQ URL loaded from Vault")

            # Celery result backend (Redis)
            redis_secrets = vault.get_secret("cache/redis")
            if redis_secrets:
                password = redis_secrets['password']
                host = redis_secrets['host']
                port = redis_secrets['port']
                self.CELERY_RESULT_BACKEND = f"redis://:{password}@{host}:{port}/4"

            # Security secrets
            jwt_secret = vault.get_secret("security/jwt", "secret_key")
            if jwt_secret:
                self.JWT_SECRET_KEY = jwt_secret
                logger.debug("✅ JWT secret loaded from Vault")

            app_secret = vault.get_secret("security/app_secret", "key")
            if app_secret:
                self.SECRET_KEY = app_secret
                logger.debug("✅ App secret loaded from Vault")

            gateway_key = vault.get_secret("security/gateway", "api_key")
            if gateway_key:
                self.GATEWAY_API_KEY = gateway_key
                logger.debug("✅ Gateway API key loaded from Vault")

            # OpenAI
            openai_key = vault.get_secret("openai", "api_key")
            if openai_key:
                self.OPENAI_API_KEY = openai_key
                logger.debug("✅ OpenAI API key loaded from Vault")

            openai_model = vault.get_secret("openai", "model")
            if openai_model:
                self.OPENAI_MODEL = openai_model

            logger.info("✅ All secrets loaded from Vault successfully")

        except ImportError:
            logger.warning("⚠️ Vault client not available (hvac not installed?) - using environment fallback")
        except Exception as e:
            logger.error(f"❌ Error loading secrets from Vault: {e}")
            logger.warning("⚠️ Falling back to environment variables")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
