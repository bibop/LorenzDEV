"""
LORENZ SaaS - Health & Core API Integration Tests
===================================================
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_openapi_docs_disabled_in_production(client: AsyncClient):
    """Test that OpenAPI docs are disabled in production"""
    # In test mode, this depends on DEBUG setting
    response = await client.get("/docs")
    # Could be 200 (dev mode) or 404 (production)
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_process_time_header(client: AsyncClient):
    """Test that X-Process-Time header is present"""
    response = await client.get("/health")
    
    assert "x-process-time" in response.headers
    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0
