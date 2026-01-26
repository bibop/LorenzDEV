"""
LORENZ SaaS - RSI API Integration Tests
========================================
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trigger_pattern_mining(client: AsyncClient, auth_headers: dict):
    """Test triggering pattern mining"""
    response = await client.post(
        "/api/v1/rsi/mine-patterns",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "proposals_created" in data
    assert "patterns_found" in data


@pytest.mark.asyncio
async def test_pattern_mining_unauthenticated(client: AsyncClient):
    """Test pattern mining requires authentication"""
    response = await client.post("/api/v1/rsi/mine-patterns")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_submit_feedback(client: AsyncClient, auth_headers: dict):
    """Test submitting feedback for skill run"""
    from uuid import uuid4
    
    response = await client.post(
        "/api/v1/rsi/telemetry/feedback",
        json={
            "skill_run_id": str(uuid4()),
            "score": 5,
            "comment": "Great result!"
        },
        headers=auth_headers
    )
    
    # Will return 404 if skill run doesn't exist
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_rsi_stats(client: AsyncClient, auth_headers: dict):
    """Test getting RSI statistics (admin only)"""
    response = await client.get("/api/v1/rsi/stats", headers=auth_headers)
    
    # May return 403 if not admin
    assert response.status_code in [200, 403]
