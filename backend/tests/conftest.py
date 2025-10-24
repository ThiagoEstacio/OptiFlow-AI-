"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def test_client(test_db_session) -> TestClient:
    """Create test client with database override"""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_test_client(test_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_annotation_data():
    """Sample annotation data for testing"""
    return {
        "type": "comment",
        "priority": "medium",
        "title": "Test Annotation",
        "description": "This is a test annotation",
        "start_time": "2024-01-01T00:00:00Z",
        "tags": ["test", "annotation"],
        "is_public": True
    }


@pytest.fixture
def sample_timeseries_data():
    """Sample time series data for testing"""
    return [
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "value": 42.5,
            "quality": "good"
        },
        {
            "timestamp": "2024-01-01T00:05:00Z",
            "value": 43.2,
            "quality": "good"
        },
        {
            "timestamp": "2024-01-01T00:10:00Z",
            "value": 41.8,
            "quality": "good"
        }
    ]
