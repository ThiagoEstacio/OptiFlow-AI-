"""
HashiCorp Vault Client for OptiFlow Platform

Provides async interface to retrieve secrets from Vault with caching and fallback support.
"""

import os
import logging
from typing import Dict, Any, Optional
import hvac
from hvac.exceptions import VaultError

logger = logging.getLogger(__name__)


class VaultClient:
    """HashiCorp Vault client for secret management."""

    def __init__(
        self,
        vault_addr: str = "http://vault:8200",
        vault_token: Optional[str] = None,
        mount_point: str = "optiflow"
    ):
        """
        Initialize Vault client.

        Args:
            vault_addr: Vault server address
            vault_token: Vault authentication token
            mount_point: KV secrets engine mount point
        """
        self.vault_addr = vault_addr
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN", "optiflow-dev-root-token")
        self.mount_point = mount_point

        self.client = hvac.Client(
            url=self.vault_addr,
            token=self.vault_token
        )

        self._cache: Dict[str, Any] = {}
        self._authenticated = False

        # Try to authenticate
        try:
            self._authenticated = self.client.is_authenticated()
            if self._authenticated:
                logger.info(f"✅ VaultClient connected: {vault_addr}")
            else:
                logger.warning(f"⚠️ VaultClient failed to authenticate: {vault_addr}")
        except Exception as e:
            logger.error(f"❌ VaultClient connection error: {e}")

    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._authenticated

    def get_secret(self, path: str, key: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve secret from Vault.

        Args:
            path: Secret path (e.g., "openai", "database/postgres")
            key: Specific key within secret (if None, returns all)

        Returns:
            Secret value or dict of all keys

        Example:
            >>> vault.get_secret("openai", "api_key")
            "sk-proj-..."

            >>> vault.get_secret("database/postgres")
            {"user": "optiflow", "password": "...", ...}
        """
        # Check cache first
        cache_key = f"{path}:{key}" if key else path
        if cache_key in self._cache:
            logger.debug(f"Vault cache hit: {cache_key}")
            return self._cache[cache_key]

        if not self._authenticated:
            logger.warning(f"Vault not authenticated, cannot retrieve {path}")
            return None

        try:
            # Read from Vault KV v2
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )

            data = response['data']['data']

            # Cache result
            if key:
                value = data.get(key)
                self._cache[cache_key] = value
                logger.debug(f"Vault secret retrieved: {path}/{key}")
                return value
            else:
                self._cache[cache_key] = data
                logger.debug(f"Vault secrets retrieved: {path}")
                return data

        except VaultError as e:
            logger.error(f"Vault error reading {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading {path}: {e}")
            return None

    def get_database_url(self, db_type: str = "postgres") -> Optional[str]:
        """
        Build database URL from Vault secrets.

        Args:
            db_type: "postgres" or "influxdb"

        Returns:
            Database connection URL
        """
        if db_type == "postgres":
            secrets = self.get_secret("database/postgres")
            if secrets:
                user = secrets['user']
                password = secrets['password']
                host = secrets['host']
                port = secrets['port']
                database = secrets['database']
                return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

        elif db_type == "influxdb":
            return self.get_secret("database/influxdb", "url")

        return None

    def get_redis_url(self) -> Optional[str]:
        """Build Redis URL from Vault secrets."""
        secrets = self.get_secret("cache/redis")
        if secrets:
            password = secrets['password']
            host = secrets['host']
            port = secrets['port']
            db = secrets['db']
            return f"redis://:{password}@{host}:{port}/{db}"
        return None

    def get_rabbitmq_url(self) -> Optional[str]:
        """Build RabbitMQ URL from Vault secrets."""
        secrets = self.get_secret("messaging/rabbitmq")
        if secrets:
            user = secrets['user']
            password = secrets['password']
            host = secrets['host']
            port = secrets['port']
            vhost = secrets['vhost']
            return f"amqp://{user}:{password}@{host}:{port}{vhost}"
        return None

    def clear_cache(self):
        """Clear cached secrets (force reload)."""
        self._cache.clear()
        logger.info("Vault cache cleared")


# Global Vault client instance
_vault_client: Optional[VaultClient] = None


def get_vault_client() -> VaultClient:
    """Get or create global Vault client."""
    global _vault_client

    if _vault_client is None:
        vault_addr = os.getenv("VAULT_ADDR", "http://vault:8200")
        vault_token = os.getenv("VAULT_TOKEN", "optiflow-dev-root-token")
        _vault_client = VaultClient(vault_addr=vault_addr, vault_token=vault_token)

    return _vault_client


def get_secret_or_env(vault_path: str, vault_key: str, env_var: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get secret from Vault with fallback to environment variable.

    Args:
        vault_path: Vault secret path
        vault_key: Vault secret key
        env_var: Environment variable name (fallback)
        default: Default value if both fail

    Returns:
        Secret value from Vault, env var, or default

    Example:
        >>> get_secret_or_env("openai", "api_key", "OPENAI_API_KEY")
        "sk-proj-..."  # from Vault

        >>> # If Vault fails:
        "sk-proj-..."  # from OPENAI_API_KEY env var
    """
    vault_enabled = os.getenv("VAULT_ENABLED", "true").lower() == "true"

    if vault_enabled:
        try:
            vault = get_vault_client()
            if vault.is_authenticated():
                value = vault.get_secret(vault_path, vault_key)
                if value is not None:
                    logger.debug(f"Using Vault secret: {vault_path}/{vault_key}")
                    return value
        except Exception as e:
            logger.warning(f"Failed to get Vault secret {vault_path}/{vault_key}: {e}")

    # Fallback to environment variable
    env_value = os.getenv(env_var)
    if env_value:
        logger.debug(f"Using env var: {env_var}")
        return env_value

    # Final fallback to default
    if default:
        logger.debug(f"Using default value for {env_var}")
    return default
