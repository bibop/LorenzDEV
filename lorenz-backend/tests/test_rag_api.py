"""
LORENZ SaaS - RAG API Integration Tests
========================================
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rag_search(client: AsyncClient, auth_headers: dict):
    """Test RAG search endpoint"""
    response = await client.post(
        "/api/v1/rag/search",
        json={
            "query": "test query",
            "limit": 5,
            "use_reranking": False
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert "query" in data


@pytest.mark.asyncio
async def test_rag_simple_search(client: AsyncClient, auth_headers: dict):
    """Test simple RAG search endpoint"""
    response = await client.get(
        "/api/v1/rag/search/simple",
        params={"q": "test", "limit": 5},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_rag_search_unauthenticated(client: AsyncClient):
    """Test RAG search requires authentication"""
    response = await client.post(
        "/api/v1/rag/search",
        json={"query": "test"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, auth_headers: dict):
    """Test listing indexed documents"""
    response = await client.get("/api/v1/rag/documents", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_index_text_content(client: AsyncClient, auth_headers: dict):
    """Test indexing text content directly"""
    response = await client.post(
        "/api/v1/rag/documents/index-text",
        params={
            "title": "Test Document",
            "content": "This is a test document for LORENZ RAG system.",
            "source_type": "note"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data


@pytest.mark.asyncio
async def test_get_rag_stats(client: AsyncClient, auth_headers: dict):
    """Test getting RAG statistics"""
    response = await client.get("/api/v1/rag/stats", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "embedding_model" in data


@pytest.mark.asyncio
async def test_get_supported_formats(client: AsyncClient, auth_headers: dict):
    """Test getting supported file formats"""
    response = await client.get("/api/v1/rag/formats", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "extensions" in data
    assert "max_file_size_mb" in data


@pytest.mark.asyncio
async def test_get_context_for_query(client: AsyncClient, auth_headers: dict):
    """Test getting formatted context for a query"""
    response = await client.post(
        "/api/v1/rag/context",
        params={"query": "test query", "max_tokens": 1000},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "context" in data
    assert "query" in data
