"""
Pytest configuration and fixtures for SmartPort tests
"""
import os
import sys
import tempfile

# Configure test environment BEFORE any app imports
TEST_MODELS_DIR = tempfile.mkdtemp(prefix='optiflow_test_models_')
os.environ['ML_MODELS_DIR'] = TEST_MODELS_DIR
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
from httpx import AsyncClient
from uuid import uuid4

# Import SQLAlchemy types for UUID support
from sqlalchemy import TypeDecorator, String, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(32).
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid.UUID):
                return value.hex
            else:
                return uuid.UUID(value).hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)


# Monkey-patch UUID type for SQLite compatibility
import sqlalchemy
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import TypeEngine

# Register UUID type compiler for SQLite - this must happen BEFORE importing app
class SQLiteUUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
        return value

# Patch SQLite to handle PostgreSQL UUID type using compiles decorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.compiler import compiles

@compiles(UUID, 'sqlite')
def compile_uuid_sqlite(element, compiler, **kw):
    """Compile UUID type as CHAR(36) for SQLite."""
    return "CHAR(36)"

# Also handle JSONB for SQLite
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(element, compiler, **kw):
    """Compile JSONB type as TEXT for SQLite."""
    return "TEXT"

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.models.user import User
from app.models.organization import Organization, Site
from app.models.device import Device
from app.models.tag import Tag
from app.core.security import get_password_hash, create_access_token


# Test database URL (SQLite in-memory for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override"""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_organization(test_db) -> Organization:
    """Create test organization"""
    org = Organization(
        id=uuid4(),
        name="Test Organization",
        slug="test-organization",
        is_active=True
    )
    test_db.add(org)
    await test_db.commit()
    await test_db.refresh(org)
    return org


@pytest.fixture
async def test_user(test_db, test_organization) -> User:
    """Create test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=False,
        organization_id=test_organization.id
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def test_token(test_user) -> str:
    """Create test JWT token"""
    return create_access_token(subject=str(test_user.id))


@pytest.fixture
def auth_headers(test_token) -> dict:
    """Create authentication headers"""
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
async def test_site(test_db, test_organization) -> Site:
    """Create test site"""
    site = Site(
        id=uuid4(),
        name="Test Port",
        site_type="smartport",
        organization_id=test_organization.id,
        latitude=-23.5505,
        longitude=-46.6333,
        is_active=True
    )
    test_db.add(site)
    await test_db.commit()
    await test_db.refresh(site)
    return site


@pytest.fixture
async def test_device(test_db, test_site) -> Device:
    """Create test device"""
    device = Device(
        id=uuid4(),
        name="Test PLC",
        protocol="modbus_tcp",
        ip_address="192.168.1.100",
        port=502,
        site_id=test_site.id,
        enabled=True,
        scan_rate=1000
    )
    test_db.add(device)
    await test_db.commit()
    await test_db.refresh(device)
    return device


@pytest.fixture
async def test_tag(test_db, test_device) -> Tag:
    """Create test tag"""
    tag = Tag(
        id=uuid4(),
        name="Test_Temperature",
        address="40001",
        data_type="FLOAT",
        device_id=test_device.id,
        unit="°C",
        enabled=True,
        log_enabled=True
    )
    test_db.add(tag)
    await test_db.commit()
    await test_db.refresh(tag)
    return tag
