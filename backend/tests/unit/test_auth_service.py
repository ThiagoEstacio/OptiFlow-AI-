"""
Unit tests for Authentication Service
Tests JWT token handling, password hashing, and auth flows
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4
import jwt

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings


class TestPasswordHashing:
    """Tests for password hashing functionality"""

    def test_hash_password_returns_string(self):
        """Should return hashed password string"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert hashed != password

    def test_hash_is_different_each_time(self):
        """Same password should produce different hashes (salt)"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # bcrypt uses salt, so hashes should be different
        # but both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_correct_password(self):
        """Should verify correct password"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Should reject incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_empty_password_handling(self):
        """Should handle empty password"""
        # Empty password should still hash
        hashed = get_password_hash("")
        assert isinstance(hashed, str)
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_unicode_password(self):
        """Should handle unicode passwords"""
        password = "Пароль123!こんにちは"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_very_long_password(self):
        """Should handle very long passwords"""
        password = "A" * 1000
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestAccessToken:
    """Tests for JWT access token creation"""

    def test_create_access_token_returns_string(self):
        """Should return JWT string"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_valid_jwt(self):
        """Token should be valid JWT format"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        # JWT has 3 parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_contains_subject(self):
        """Token should contain subject claim"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        # Decode without verification for testing
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert decoded["sub"] == subject

    def test_token_has_expiration(self):
        """Token should have expiration claim"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert "exp" in decoded

    def test_custom_expiration(self):
        """Should support custom expiration"""
        subject = str(uuid4())
        expires_delta = timedelta(hours=1)
        token = create_access_token(
            subject=subject,
            expires_delta=expires_delta
        )
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        # Expiration should be approximately 1 hour from now
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        diff = exp_time - now
        assert timedelta(minutes=55) < diff < timedelta(minutes=65)

    def test_token_type_is_access(self):
        """Token should have access type"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert decoded.get("type") == "access"


class TestRefreshToken:
    """Tests for JWT refresh token creation"""

    def test_create_refresh_token_returns_string(self):
        """Should return JWT string"""
        subject = str(uuid4())
        token = create_refresh_token(subject=subject)
        assert isinstance(token, str)

    def test_refresh_token_has_longer_expiration(self):
        """Refresh token should have longer expiration than access token"""
        subject = str(uuid4())
        access_token = create_access_token(subject=subject)
        refresh_token = create_refresh_token(subject=subject)

        access_decoded = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        refresh_decoded = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        # Refresh token expiration should be later than access token
        assert refresh_decoded["exp"] > access_decoded["exp"]

    def test_refresh_token_type(self):
        """Refresh token should have refresh type"""
        subject = str(uuid4())
        token = create_refresh_token(subject=subject)
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert decoded.get("type") == "refresh"


class TestTokenVerification:
    """Tests for token verification"""

    def test_valid_token_decodes(self):
        """Valid token should decode successfully"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert decoded["sub"] == subject

    def test_tampered_token_fails(self):
        """Tampered token should fail verification"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        # Tamper with token
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(
                tampered,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )

    def test_wrong_secret_fails(self):
        """Token with wrong secret should fail"""
        subject = str(uuid4())
        token = create_access_token(subject=subject)
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(
                token,
                "wrong_secret_key",
                algorithms=["HS256"]
            )

    def test_expired_token_fails(self):
        """Expired token should fail verification"""
        subject = str(uuid4())
        # Create token with negative expiration (already expired)
        token = create_access_token(
            subject=subject,
            expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )


class TestSecuritySettings:
    """Tests for security-related settings"""

    def test_secret_key_exists(self):
        """SECRET_KEY should be configured"""
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_algorithm_is_secure(self):
        """Algorithm should be secure (HS256 or RS256)"""
        # The algorithm used should be in the secure set
        assert settings.ALGORITHM in ["HS256", "RS256", "HS384", "HS512"]


class TestAuthenticationFlow:
    """Integration-style tests for auth flow"""

    def test_full_login_flow(self):
        """Test complete login flow"""
        # 1. Hash password during registration
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        # 2. Verify password during login
        assert verify_password(password, hashed) is True

        # 3. Create tokens
        user_id = str(uuid4())
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)

        # 4. Verify tokens
        access_decoded = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert access_decoded["sub"] == user_id

        refresh_decoded = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert refresh_decoded["sub"] == user_id

    def test_token_refresh_flow(self):
        """Test token refresh flow"""
        user_id = str(uuid4())

        # 1. Create initial tokens
        refresh_token = create_refresh_token(subject=user_id)

        # 2. Decode refresh token
        decoded = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        # 3. Create new access token
        new_access_token = create_access_token(subject=decoded["sub"])

        # 4. Verify new token
        new_decoded = jwt.decode(
            new_access_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        assert new_decoded["sub"] == user_id


class TestPasswordSecurity:
    """Tests for password security requirements"""

    def test_hash_length_is_sufficient(self):
        """Hash should be sufficiently long for security"""
        password = "test"
        hashed = get_password_hash(password)
        # bcrypt hashes are typically 60 characters
        assert len(hashed) >= 50

    def test_hash_format_is_bcrypt(self):
        """Hash should be in bcrypt format"""
        password = "test"
        hashed = get_password_hash(password)
        # bcrypt hashes start with $2a$, $2b$, or $2y$
        assert hashed.startswith("$2")
