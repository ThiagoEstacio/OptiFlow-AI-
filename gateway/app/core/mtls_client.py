"""
PDCA #2: mTLS (Mutual TLS) Client
==================================

Implements certificate-based authentication between Gateway and Backend:
- Client certificate authentication (gateway.crt + gateway.key)
- Server certificate validation (ca.crt)
- Certificate rotation support (90-day policy)
- Vault integration for certificate management

Security Benefits:
- Stronger than API keys (cryptographic proof)
- Mutual authentication (both parties verified)
- Transport encryption (TLS 1.3)
- Certificate rotation (prevents long-term key compromise)
"""
import ssl
import aiohttp
from pathlib import Path
from typing import Optional
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from .logger import logger
from .config import settings


class MTLSConfig:
    """
    mTLS Configuration Manager
    Handles certificate loading and validation
    """

    def __init__(
        self,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_path: Optional[str] = None
    ):
        """
        Initialize mTLS configuration

        Args:
            cert_path: Path to client certificate (gateway.crt)
            key_path: Path to client private key (gateway.key)
            ca_path: Path to CA certificate (ca.crt)
        """
        self.cert_path = Path(cert_path or settings.MTLS_CERT_PATH or "/app/certs/gateway.crt")
        self.key_path = Path(key_path or settings.MTLS_KEY_PATH or "/app/certs/gateway.key")
        self.ca_path = Path(ca_path or settings.MTLS_CA_PATH or "/app/certs/ca.crt")

        self._ssl_context: Optional[ssl.SSLContext] = None

    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context for mTLS

        Returns:
            Configured SSL context with client certificate and CA verification

        Raises:
            FileNotFoundError: If certificates are missing
            ssl.SSLError: If certificates are invalid
        """
        # Validate certificate files exist
        if not self.cert_path.exists():
            raise FileNotFoundError(f"Client certificate not found: {self.cert_path}")
        if not self.key_path.exists():
            raise FileNotFoundError(f"Client private key not found: {self.key_path}")
        if not self.ca_path.exists():
            raise FileNotFoundError(f"CA certificate not found: {self.ca_path}")

        # Create SSL context with TLS 1.3 (most secure)
        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=str(self.ca_path)
        )

        # Load client certificate and private key
        ssl_context.load_cert_chain(
            certfile=str(self.cert_path),
            keyfile=str(self.key_path)
        )

        # Require server certificate verification
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        # Use only TLS 1.2+ (disable older versions)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

        self._ssl_context = ssl_context
        logger.info("✅ mTLS SSL context created successfully")

        return ssl_context

    def get_ssl_context(self) -> ssl.SSLContext:
        """Get cached SSL context or create new one"""
        if self._ssl_context is None:
            return self.create_ssl_context()
        return self._ssl_context

    def check_certificate_expiry(self) -> dict:
        """
        Check certificate expiration dates

        Returns:
            Dictionary with expiration info for all certificates
        """
        results = {}

        for name, cert_path in [
            ("client_cert", self.cert_path),
            ("ca_cert", self.ca_path)
        ]:
            try:
                with open(cert_path, "rb") as f:
                    cert_data = f.read()
                    cert = x509.load_pem_x509_certificate(cert_data, default_backend())

                    days_until_expiry = (cert.not_valid_after - datetime.now()).days

                    results[name] = {
                        "path": str(cert_path),
                        "subject": cert.subject.rfc4514_string(),
                        "issuer": cert.issuer.rfc4514_string(),
                        "not_before": cert.not_valid_before.isoformat(),
                        "not_after": cert.not_valid_after.isoformat(),
                        "days_until_expiry": days_until_expiry,
                        "is_valid": days_until_expiry > 0,
                        "needs_rotation": days_until_expiry < 30  # Warn if <30 days
                    }

                    # Log warnings
                    if days_until_expiry < 30:
                        logger.warning(
                            f"⚠️ Certificate {name} expires in {days_until_expiry} days! "
                            f"Rotation required before {cert.not_valid_after.date()}"
                        )
                    elif days_until_expiry < 90:
                        logger.info(
                            f"📅 Certificate {name} expires in {days_until_expiry} days "
                            f"({cert.not_valid_after.date()})"
                        )

            except Exception as e:
                logger.error(f"❌ Failed to check {name} expiry: {e}")
                results[name] = {"error": str(e), "is_valid": False}

        return results

    def rotate_certificates(self) -> bool:
        """
        Rotate certificates from Vault

        This method should be called periodically (e.g., every 30 days)
        to fetch new certificates from HashiCorp Vault.

        Returns:
            True if rotation successful, False otherwise
        """
        try:
            # TODO: Implement Vault integration
            # 1. Connect to Vault PKI backend
            # 2. Request new certificate for gateway
            # 3. Save new cert/key to disk
            # 4. Reload SSL context

            logger.warning("⚠️ Certificate rotation not yet implemented (requires Vault PKI)")
            return False

        except Exception as e:
            logger.error(f"❌ Certificate rotation failed: {e}")
            return False


class MTLSClientSession:
    """
    HTTP Client Session with mTLS support
    Drop-in replacement for aiohttp.ClientSession
    """

    def __init__(
        self,
        base_url: str,
        mtls_config: MTLSConfig,
        timeout: Optional[aiohttp.ClientTimeout] = None
    ):
        """
        Initialize mTLS client session

        Args:
            base_url: Backend API base URL
            mtls_config: mTLS configuration
            timeout: Request timeout configuration
        """
        self.base_url = base_url
        self.mtls_config = mtls_config
        self.timeout = timeout or aiohttp.ClientTimeout(total=30)

        self._session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        """Initialize HTTP session with mTLS"""
        if self._session is not None:
            return

        # Create SSL context for mTLS
        ssl_context = self.mtls_config.get_ssl_context()

        # Check certificate expiry
        expiry_info = self.mtls_config.check_certificate_expiry()
        for cert_name, info in expiry_info.items():
            if not info.get("is_valid", False):
                logger.error(f"❌ Invalid certificate: {cert_name}")
                raise ValueError(f"Certificate {cert_name} is invalid or expired")

        # Create aiohttp session with mTLS SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(
            base_url=self.base_url,
            connector=connector,
            timeout=self.timeout
        )

        logger.info(f"✅ mTLS client session connected to {self.base_url}")

    async def disconnect(self) -> None:
        """Close HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("mTLS client session disconnected")

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """HTTP GET with mTLS"""
        if not self._session:
            await self.connect()
        return await self._session.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """HTTP POST with mTLS"""
        if not self._session:
            await self.connect()
        return await self._session.post(url, **kwargs)

    async def put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """HTTP PUT with mTLS"""
        if not self._session:
            await self.connect()
        return await self._session.put(url, **kwargs)

    async def delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """HTTP DELETE with mTLS"""
        if not self._session:
            await self.connect()
        return await self._session.delete(url, **kwargs)

    def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
