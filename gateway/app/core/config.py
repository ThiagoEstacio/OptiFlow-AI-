"""
Gateway Configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Gateway settings"""

    # Gateway Identity
    GATEWAY_ID: str = Field(default="gateway-001", env="GATEWAY_ID")
    GATEWAY_NAME: str = Field(default="OptiFlow Gateway", env="GATEWAY_NAME")

    # Backend API
    BACKEND_URL: str = Field(default="http://backend:8000", env="BACKEND_URL")
    BACKEND_API_KEY: Optional[str] = Field(default=None, env="BACKEND_API_KEY")

    # Database for offline buffering
    BUFFER_DB_PATH: str = Field(default="/app/data/buffer.db", env="BUFFER_DB_PATH")
    BUFFER_MAX_SIZE_MB: int = Field(default=100, env="BUFFER_MAX_SIZE_MB")

    # Collection settings
    DEFAULT_SCAN_RATE: int = Field(default=1000, env="DEFAULT_SCAN_RATE")  # milliseconds
    MAX_RETRY_ATTEMPTS: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    RETRY_DELAY: int = Field(default=5, env="RETRY_DELAY")  # seconds

    # Connection timeouts
    CONNECTION_TIMEOUT: int = Field(default=10, env="CONNECTION_TIMEOUT")  # seconds
    READ_TIMEOUT: int = Field(default=5, env="READ_TIMEOUT")  # seconds

    # Health check
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")  # seconds

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="/app/logs/gateway.log", env="LOG_FILE")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
