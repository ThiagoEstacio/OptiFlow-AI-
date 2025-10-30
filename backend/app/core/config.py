"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings"""

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
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

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

    # Gateway
    GATEWAY_API_KEY: str = "secure-gateway-api-key-change-in-production"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

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

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
