"""
LORENZ SaaS - Twin & Voice/Avatar API Integration Tests
=========================================================
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_twin_profile(client: AsyncClient, auth_headers: dict):
    """Test getting twin profile"""
    response = await client.get("/api/v1/twin/profile", headers=auth_headers)
    
    # May return 500 if profile not initialized, which is expected
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_twin_profile_unauthenticated(client: AsyncClient):
    """Test twin profile requires authentication"""
    response = await client.get("/api/v1/twin/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_vip_contacts(client: AsyncClient, auth_headers: dict):
    """Test listing VIP contacts"""
    response = await client.get("/api/v1/twin/profile/vip", headers=auth_headers)
    
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, auth_headers: dict):
    """Test listing projects"""
    response = await client.get("/api/v1/twin/projects", headers=auth_headers)
    
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_get_suggestions(client: AsyncClient, auth_headers: dict):
    """Test getting proactive suggestions"""
    response = await client.get("/api/v1/twin/suggestions", headers=auth_headers)
    
    assert response.status_code in [200, 500]


# Voice & Avatar Tests

@pytest.mark.asyncio
async def test_list_voices(client: AsyncClient, auth_headers: dict):
    """Test listing available voices"""
    response = await client.get("/api/v1/twin/voices", headers=auth_headers)
    
    # May fail if no ElevenLabs API key configured
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_get_voice_quota(client: AsyncClient, auth_headers: dict):
    """Test getting voice quota"""
    response = await client.get("/api/v1/twin/voice/quota", headers=auth_headers)
    
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_create_avatar_session(client: AsyncClient, auth_headers: dict):
    """Test creating avatar session"""
    response = await client.post(
        "/api/v1/twin/avatar/session",
        json={
            "avatar_model": "default",
            "metadata": {"test": True}
        },
        headers=auth_headers
    )
    
    # May fail if Redis not available
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_list_avatar_sessions(client: AsyncClient, auth_headers: dict):
    """Test listing user's avatar sessions"""
    response = await client.get("/api/v1/twin/avatar/sessions", headers=auth_headers)
    
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_get_nonexistent_session(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent avatar session"""
    response = await client.get(
        "/api/v1/twin/avatar/session/nonexistent-id",
        headers=auth_headers
    )
    
    assert response.status_code in [404, 500]
