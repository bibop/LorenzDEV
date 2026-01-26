"""
LORENZ SaaS - Skills API Integration Tests
============================================
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_skills(client: AsyncClient, auth_headers: dict):
    """Test listing skills endpoint"""
    response = await client.get("/api/v1/skills", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert "total" in data
    assert "enabled" in data
    assert isinstance(data["skills"], list)


@pytest.mark.asyncio
async def test_list_skills_unauthenticated(client: AsyncClient):
    """Test skills endpoint requires authentication"""
    response = await client.get("/api/v1/skills")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_skills_by_category(client: AsyncClient, auth_headers: dict):
    """Test filtering skills by category"""
    response = await client.get(
        "/api/v1/skills",
        params={"category": "creative"},
        headers=auth_headers
    )
    
    assert response.status_code in [200, 400]  # 400 if category doesn't exist


@pytest.mark.asyncio
async def test_get_skill_categories(client: AsyncClient, auth_headers: dict):
    """Test getting skill categories"""
    response = await client.get("/api/v1/skills/categories", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_execute_skill_not_found(client: AsyncClient, auth_headers: dict):
    """Test executing non-existent skill"""
    response = await client.post(
        "/api/v1/skills/execute",
        json={"skill_name": "nonexistent_skill", "parameters": {}},
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_propose_emergent_skill(client: AsyncClient, auth_headers: dict):
    """Test proposing an emergent skill"""
    response = await client.post(
        "/api/v1/skills/emergent/propose",
        json={
            "suggested_name": "test_workflow",
            "reasoning": "Detected repeated pattern in user actions",
            "confidence": 0.85,
            "proposed_schema": {
                "type": "function",
                "function": {
                    "name": "test_workflow",
                    "description": "Test workflow skill",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["suggested_name"] == "test_workflow"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_pending_proposals(client: AsyncClient, auth_headers: dict):
    """Test listing pending skill proposals"""
    response = await client.get(
        "/api/v1/skills/emergent/proposals",
        params={"status": "pending"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
