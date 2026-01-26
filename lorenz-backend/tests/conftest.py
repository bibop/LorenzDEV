"""
LORENZ SaaS - Test Configuration
=================================

Pytest fixtures and configuration for integration tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid import uuid4

from app.main import app
from app.database import get_db, Base
from app.models import User, Tenant
from app.config import settings


# Test database URL (use separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/lorenz", "/lorenz_test")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create test tenant"""
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        slug="test-tenant",
        plan="professional"
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create test user"""
    from app.services.auth import hash_password
    
    user = User(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="test@lorenz.ai",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        email_verified=True,
        role="owner"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_token(test_user: User) -> str:
    """Generate JWT token for test user"""
    from app.services.auth import create_access_token
    
    return create_access_token(subject=str(test_user.id))


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Authentication headers for requests"""
    return {"Authorization": f"Bearer {auth_token}"}
